import json
import time
from hashlib import sha256
from typing import Dict, List, Literal, Optional, Tuple, Union

from loguru import logger

from ..core.base import (
    BlindedMessage,
    BlindedSignature,
    DiscreetLogContract,
    DlcBadInput,
    DlcOutcome,
    DlcPayoutWitness,
    Method,
    MintKeyset,
    Proof,
    Unit,
)
from ..core.crypto import b_dhke
from ..core.crypto.dlc import (
    merkle_verify,
    verify_payout_secret,
    verify_payout_signature,
)
from ..core.crypto.secp import PrivateKey, PublicKey
from ..core.db import Connection, Database
from ..core.errors import (
    CashuError,
    DlcPayoutFail,
    DlcSettlementFail,
    DlcVerificationFail,
    NoSecretInProofsError,
    NotAllowedError,
    SecretTooLongError,
    TransactionError,
    TransactionUnitError,
)
from ..core.settings import settings
from ..lightning.base import LightningBackend
from ..mint.crud import LedgerCrud
from .conditions import LedgerSpendingConditions
from .db.read import DbReadHelper
from .db.write import DbWriteHelper
from .dlc import LedgerDLC
from .protocols import SupportsBackends, SupportsDb, SupportsKeysets


class LedgerVerification(
    LedgerSpendingConditions, LedgerDLC, SupportsKeysets, SupportsDb, SupportsBackends
):
    """Verification functions for the ledger."""

    keyset: MintKeyset
    keysets: Dict[str, MintKeyset]
    crud: LedgerCrud
    db: Database
    db_read: DbReadHelper
    db_write: DbWriteHelper
    lightning: Dict[Unit, LightningBackend]

    async def verify_inputs_and_outputs(
        self,
        *,
        proofs: List[Proof],
        outputs: Optional[List[BlindedMessage]] = None,
        conn: Optional[Connection] = None,
    ):
        """Checks all proofs and outputs for validity.

        Args:
            proofs (List[Proof]): List of proofs to check.
            outputs (Optional[List[BlindedMessage]], optional): List of outputs to check.
                Must be provided for a swap but not for a melt. Defaults to None.
            conn (Optional[Connection], optional): Database connection. Defaults to None.

        Raises:
            Exception: Scripts did not validate.
            Exception: Criteria for provided secrets not met.
            Exception: Duplicate proofs provided.
            Exception: BDHKE verification failed.
        """
        # Verify inputs
        if not proofs:
            raise TransactionError("no proofs provided.")
        # Verify amounts of inputs
        if not all([self._verify_amount(p.amount) for p in proofs]):
            raise TransactionError("invalid amount.")
        # Verify secret criteria
        if not all([self._verify_secret_criteria(p) for p in proofs]):
            raise TransactionError("secrets do not match criteria.")
        # verify that only unique proofs were used
        if not self._verify_no_duplicate_proofs(proofs):
            raise TransactionError("duplicate proofs.")
        # Verify ecash signatures
        if not all([self._verify_proof_bdhke(p) for p in proofs]):
            raise TransactionError("could not verify proofs.")
        # Verify input spending conditions
        if not all([self._verify_input_spending_conditions(p) for p in proofs]):
            raise TransactionError("validation of input spending conditions failed.")

        if outputs is None:
            # If no outputs are provided, we are melting
            return

        # Verify input and output amounts
        self._verify_equation_balanced(proofs, outputs)

        # Verify outputs
        await self._verify_outputs(outputs, conn=conn)

        # Verify inputs and outputs together
        if not self._verify_input_output_amounts(proofs, outputs):
            raise TransactionError("input amounts less than output.")
        # Verify that input keyset units are the same as output keyset unit
        # We have previously verified that all outputs have the same keyset id in `_verify_outputs`
        assert outputs[0].id, "output id not set"
        if not all(
            [
                self.keysets[p.id].unit == self.keysets[outputs[0].id].unit
                for p in proofs
            ]
        ):
            raise TransactionError("input and output keysets have different units.")

        # Verify output spending conditions
        if outputs and not self._verify_output_spending_conditions(proofs, outputs):
            raise TransactionError("validation of output spending conditions failed.")

    async def _verify_outputs(
        self,
        outputs: List[BlindedMessage],
        skip_amount_check=False,
        conn: Optional[Connection] = None,
    ):
        """Verify that the outputs are valid."""
        logger.trace(f"Verifying {len(outputs)} outputs.")
        if not outputs:
            raise TransactionError("no outputs provided.")
        # Verify all outputs have the same keyset id
        if not all([o.id == outputs[0].id for o in outputs]):
            raise TransactionError("outputs have different keyset ids.")
        # Verify that the keyset id is known and active
        if outputs[0].id not in self.keysets:
            raise TransactionError("keyset id unknown.")
        if not self.keysets[outputs[0].id].active:
            raise TransactionError("keyset id inactive.")
        # Verify amounts of outputs
        # we skip the amount check for NUT-8 change outputs (which can have amount 0)
        if not skip_amount_check:
            if not all([self._verify_amount(o.amount) for o in outputs]):
                raise TransactionError("invalid amount.")
        # verify that only unique outputs were used
        if not self._verify_no_duplicate_outputs(outputs):
            raise TransactionError("duplicate outputs.")
        # verify that outputs have not been signed previously
        signed_before = await self._check_outputs_issued_before(outputs, conn)
        if any(signed_before):
            raise TransactionError("outputs have already been signed before.")
        logger.trace(f"Verified {len(outputs)} outputs.")

    async def _check_outputs_issued_before(
        self,
        outputs: List[BlindedMessage],
        conn: Optional[Connection] = None,
    ) -> List[bool]:
        """Checks whether the provided outputs have previously been signed by the mint
        (which would lead to a duplication error later when trying to store these outputs again).

        Args:
            outputs (List[BlindedMessage]): Outputs to check

        Returns:
            result (List[bool]): Whether outputs are already present in the database.
        """
        async with self.db.get_connection(conn) as conn:
            promises = await self.crud.get_promises(
                b_s=[output.B_ for output in outputs], db=self.db, conn=conn
            )
        return [True if promise else False for promise in promises]

    def _verify_secret_criteria(self, proof: Proof) -> Literal[True]:
        """Verifies that a secret is present and is not too long (DOS prevention)."""
        if proof.secret is None or proof.secret == "":
            raise NoSecretInProofsError()
        if len(proof.secret) > settings.mint_max_secret_length:
            raise SecretTooLongError(
                f"secret too long. max: {settings.mint_max_secret_length}"
            )
        return True

    def _verify_proof_bdhke(self, proof: Proof) -> bool:
        """Verifies that the proof of promise was issued by this ledger."""
        assert proof.id in self.keysets, f"keyset {proof.id} unknown"
        logger.trace(
            f"Validating proof {proof.secret} with keyset"
            f" {self.keysets[proof.id].id}."
        )
        # use the appropriate active keyset for this proof.id
        private_key_amount = self.keysets[proof.id].private_keys[proof.amount]

        C = PublicKey(bytes.fromhex(proof.C), raw=True)
        valid = b_dhke.verify(private_key_amount, C, proof.secret)
        if valid:
            logger.trace("Proof verified.")
        else:
            logger.trace(f"Proof verification failed for {proof.secret} – {proof.C}.")
        return valid

    def _verify_input_output_amounts(
        self, inputs: List[Proof], outputs: List[BlindedMessage]
    ) -> bool:
        """Verifies that inputs have at least the same amount as outputs"""
        input_amount = sum([p.amount for p in inputs])
        output_amount = sum([o.amount for o in outputs])
        return input_amount >= output_amount

    def _verify_no_duplicate_proofs(self, proofs: List[Proof]) -> bool:
        secrets = [p.secret for p in proofs]
        if len(secrets) != len(list(set(secrets))):
            return False
        return True

    def _verify_no_duplicate_outputs(self, outputs: List[BlindedMessage]) -> bool:
        B_s = [od.B_ for od in outputs]
        if len(B_s) != len(list(set(B_s))):
            return False
        return True

    def _verify_amount(self, amount: int) -> int:
        """Any amount used should be positive and not larger than 2^MAX_ORDER."""
        valid = amount > 0 and amount < 2**settings.max_order
        if not valid:
            raise NotAllowedError(f"invalid amount: {amount}")
        return amount

    def _verify_units_match(
        self,
        proofs: List[Proof],
        outs: Union[List[BlindedSignature], List[BlindedMessage]],
    ) -> Unit:
        """Verifies that the units of the inputs and outputs match."""
        units_proofs = [self.keysets[p.id].unit for p in proofs]
        units_outputs = [self.keysets[o.id].unit for o in outs if o.id]
        if not len(set(units_proofs)) == 1:
            raise TransactionUnitError("inputs have different units.")
        if not len(set(units_outputs)) == 1:
            raise TransactionUnitError("outputs have different units.")
        if not units_proofs[0] == units_outputs[0]:
            raise TransactionUnitError("input and output keysets have different units.")
        return units_proofs[0]

    def get_fees_for_proofs(self, proofs: List[Proof]) -> int:
        if not len({self.keysets[p.id].unit for p in proofs}) == 1:
            raise TransactionUnitError("inputs have different units.")
        fee = (sum([self.keysets[p.id].input_fee_ppk for p in proofs]) + 999) // 1000
        return fee

    def _verify_equation_balanced(
        self,
        proofs: List[Proof],
        outs: List[BlindedMessage],
    ) -> None:
        """Verify that Σinputs - Σoutputs = 0.
        Outputs can be BlindedSignature or BlindedMessage.
        """
        if not proofs:
            raise TransactionError("no proofs provided.")
        if not outs:
            raise TransactionError("no outputs provided.")

        _ = self._verify_units_match(proofs, outs)
        sum_inputs = sum(self._verify_amount(p.amount) for p in proofs)
        fees_inputs = self.get_fees_for_proofs(proofs)
        sum_outputs = sum(self._verify_amount(p.amount) for p in outs)
        if not sum_outputs + fees_inputs - sum_inputs == 0:
            raise TransactionError(
                f"inputs ({sum_inputs}) - fees ({fees_inputs}) vs outputs ({sum_outputs}) are not balanced."
            )

    def _verify_and_get_unit_method(
        self, unit_str: str, method_str: str
    ) -> Tuple[Unit, Method]:
        """Verify that the unit is supported by the ledger."""
        method = Method[method_str]
        unit = Unit[unit_str]

        if not any([unit == k.unit for k in self.keysets.values()]):
            raise NotAllowedError(f"unit '{unit.name}' not supported in any keyset.")

        if not self.backends.get(method) or unit not in self.backends[method]:
            raise NotAllowedError(
                f"no support for method '{method.name}' with unit '{unit.name}'."
            )

        return unit, method

    async def _verify_dlc_amount_fees_coverage(
        self,
        funding_amount: int,
        fa_unit: str,
        proofs: List[Proof],
    ) -> int:
        """
            Verifies the sum of the inputs is enough to cover
            the funding amount + fees

            Args:
                funding_amount (int): funding amount of the contract
                fa_unit (str): ONE OF ('sat', 'msat', 'eur', 'usd', 'btc'). The unit in which funding_amount
                    should be evaluated.
                proofs: (List[Proof]): proofs to be verified

            Returns:
                (int): amount provided by the proofs

            Raises:
                TransactionError

        """
        u = self.keysets[proofs[0].id].unit
        # Verify registration's funding_amount unit is the same as the proofs
        if Unit[fa_unit] != u:
            raise TransactionError("funding amount unit is not the same as the proofs")
        fees = await self.get_dlc_fees(fa_unit)
        amount_provided = sum([p.amount for p in proofs])
        amount_needed = funding_amount + fees['base'] + (funding_amount * fees['ppk'] // 1000)
        if amount_provided < amount_needed:
            raise TransactionError("funds provided do not cover the DLC funding amount")
        return amount_provided

    async def _verify_dlc_inputs(self, dlc: DiscreetLogContract):
        """
            Verifies all inputs to the DLC

            Args:
                dlc (DiscreetLogContract): the DLC to be funded

            Raises:
                DlcVerificationFail
        """
        # After we have collected all of the errors
        # We use this to raise a DlcVerificationFail
        def raise_if_err(err):
            if len(err) > 0:
                logger.error("Failed to verify DLC inputs")
                raise DlcVerificationFail(bad_inputs=err)

        # We cannot just raise an exception if one proof fails and call it a day
        # for every proof we need to collect its index and motivation of failure
        # and report them

        # Verify inputs
        if not dlc.inputs:
            raise TransactionError("no proofs provided.")

        errors = []
        # Verify amounts of inputs
        for i, p in enumerate(dlc.inputs):
            try:
                self._verify_amount(p.amount)
            except NotAllowedError as e:
                errors.append(DlcBadInput(
                    index=i,
                    detail=e.detail
                ))
        raise_if_err(errors)

        # Verify secret criteria
        for i, p in enumerate(dlc.inputs):
            try:
                self._verify_secret_criteria(p)
            except (SecretTooLongError, NoSecretInProofsError) as e:
                errors.append(DlcBadInput(
                    index=i,
                    detail=e.detail
                ))
        raise_if_err(errors)

        # verify that only unique proofs were used
        if not self._verify_no_duplicate_proofs(dlc.inputs):
            raise TransactionError("duplicate proofs.")

        # Verify ecash signatures
        for i, p in enumerate(dlc.inputs):
            valid = False
            exc = None
            try:
                # _verify_proof_bdhke can also raise an AssertionError...
                assert self._verify_proof_bdhke(p), "invalid e-cash signature"
            except AssertionError as e:
                errors.append(DlcBadInput(
                    index=i,
                    detail=str(e)
                ))
        raise_if_err(errors)

        # Verify proofs of the same denomination
        # REASONING: proofs could be usd, eur. We don't want mixed stuff.
        u = self.keysets[dlc.inputs[0].id].unit
        for i, p in enumerate(dlc.inputs):
            if self.keysets[p.id].unit != u:
                errors.append(DlcBadInput(
                    index=i,
                    detail="all the inputs must be of the same denomination"
                ))
        raise_if_err(errors)

        for i, p in enumerate(dlc.inputs):
            valid = False
            exc = None
            try:
                valid = self._verify_input_spending_conditions(p, funding_dlc=dlc)
            except CashuError as e:
                exc = e
            if not valid:
                errors.append(DlcBadInput(
                    index=i,
                    detail=exc.detail if exc else "input spending conditions verification failed"
                ))
        raise_if_err(errors)

    async def _verify_dlc_payout(self, P: str):
        try:
            payout = json.loads(P)
            if not isinstance(payout, dict):
                raise DlcSettlementFail(detail="Provided payout structure is not a dictionary")
            if not all([isinstance(k, str) and isinstance(v, int) for k, v in payout.items()]):
                raise DlcSettlementFail(detail="Provided payout structure is not a dictionary mapping strings to integers")
            for k in payout.keys():
                try:
                    tmp = bytes.fromhex(k)
                    if tmp[0] != 0x02 and tmp[0] != 0x03:
                        logger.error(f"Provided incorrect public key: {tmp.hex()}")
                        raise DlcSettlementFail(detail="Provided payout structure contains incorrect public keys")
                    if len(tmp) != 33:
                        logger.error(f"Provided incorrect public key: {tmp.hex()}")
                        raise DlcSettlementFail(detail="Provided payout structure contains incorrect public keys: length != 33")
                except ValueError as e:
                    raise DlcSettlementFail(detail=str(e))
            for v in payout.values():
                try:
                    weight = int(v)
                    if weight < 0:
                        raise DlcSettlementFail(detail="Provided payout structure contains incorrect payout weights")
                except ValueError:
                    raise DlcSettlementFail(detail="Provided payout structure contains incorrect payout weights")
        except json.JSONDecodeError:
            raise DlcSettlementFail(detail="cannot decode the provided payout structure")

    async def _verify_dlc_inclusion(self, dlc_root: str, outcome: DlcOutcome, merkle_proof: List[str]):
        dlc_root_bytes = None
        merkle_proof_bytes = None
        P = outcome.P.encode("utf-8")
        try:
            dlc_root_bytes = bytes.fromhex(dlc_root)
            merkle_proof_bytes = [bytes.fromhex(p) for p in merkle_proof]
            logger.debug(f"{merkle_proof = }")
        except ValueError:
            raise DlcSettlementFail(detail="either dlc root or merkle proof are not a hex string")

        # Timeout verification
        if outcome.t:
            unix_epoch = int(time.time())
            if unix_epoch < outcome.t:
                raise DlcSettlementFail(detail="too early for a timeout settlement")
            K_t = b_dhke.hash_to_curve(outcome.t.to_bytes(8, "big"))
            leaf_hash = sha256(K_t.serialize(True) + P).digest()
            if not merkle_verify(dlc_root_bytes, leaf_hash, merkle_proof_bytes):
                logger.error(f"Could not verify timeout attestation and payout structure:\n{leaf_hash.hex() = }\n{dlc_root_bytes.hex()}")
                raise DlcSettlementFail(detail="could not verify inclusion of timeout + payout structure")
        # Blinded Attestation Secret verification
        elif outcome.k:
            k = None
            try:
                k = bytes.fromhex(outcome.k)
            except ValueError:
                raise DlcSettlementFail(detail="blinded attestation secret k is not a hex string")
            K = PrivateKey(k, raw=True).pubkey
            leaf_hash = sha256(K.serialize(True) + P).digest()
            if not merkle_verify(dlc_root_bytes, leaf_hash, merkle_proof_bytes):
                logger.error(f"Could not verify secret attestation and payout structure:\n{leaf_hash.hex() = }\n{dlc_root_bytes.hex()}")
                raise DlcSettlementFail(detail="could not verify inclusion of attestation secret + payout structure")
        else:
            raise DlcSettlementFail(detail="no timeout or attestation secret provided")


    async def _verify_dlc_payout_signature(self, dlc_root: str, witness: DlcPayoutWitness, pubkey_hex: str):
        dlc_root_bytes = bytes.fromhex(dlc_root)
        pubkey = PublicKey(bytes.fromhex(pubkey_hex), raw=True)

        if witness.signature:
            signature_bytes = bytes.fromhex(witness.signature)
            if not verify_payout_signature(dlc_root_bytes, signature_bytes, pubkey):
                raise DlcPayoutFail(detail="Could not verify payout signature")
        elif witness.secret:
            secret_bytes = bytes.fromhex(witness.secret)
            if not verify_payout_secret(secret_bytes, pubkey):
                raise DlcPayoutFail(detail="Could not verify payout secret")
        else:
            raise DlcPayoutFail(detail="No witness information that provides payout authentication")

