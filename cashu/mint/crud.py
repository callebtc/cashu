from abc import ABC, abstractmethod
from typing import Any, List, Optional

from ..core.base import BlindedSignature, Invoice, MintKeyset, Proof
from ..core.db import Connection, Database, table_with_schema


class LedgerCrud(ABC):
    """
    Database interface for Cashu mint.

    This class needs to be overloaded by any app that imports the Cashu mint.
    """

    @abstractmethod
    async def get_keyset(self, *args, **kwags):
        pass

    @abstractmethod
    async def get_lightning_invoice(self, *args, **kwags) -> Optional[Invoice]:
        pass

    @abstractmethod
    async def get_secrets_used(self, *args, **kwags) -> List[str]:
        pass

    @abstractmethod
    async def invalidate_proof(self, *args, **kwags) -> None:
        pass

    @abstractmethod
    async def get_proofs_pending(self, *args, **kwags) -> List[Proof]:
        pass

    @abstractmethod
    async def set_proof_pending(self, *args, **kwags) -> None:
        pass

    @abstractmethod
    async def unset_proof_pending(self, *args, **kwags) -> None:
        pass

    @abstractmethod
    async def store_keyset(self, *args, **kwags) -> None:
        pass

    @abstractmethod
    async def store_lightning_invoice(self, *args, **kwags) -> None:
        pass

    @abstractmethod
    async def store_promise(self, *args, **kwags) -> None:
        pass

    @abstractmethod
    async def get_promise(self, *args, **kwags) -> Optional[BlindedSignature]:
        pass

    @abstractmethod
    async def update_lightning_invoice(self, *args, **kwags) -> None:
        pass


class LedgerCrudSqlite(LedgerCrud):
    """Implementation of LedgerCrud for sqlite.

    Args:
        LedgerCrud (ABC): Abstract base class for LedgerCrud.
    """

    async def store_promise(
        self,
        *,
        db: Database,
        amount: int,
        B_: str,
        C_: str,
        id: str,
        e: str = "",
        s: str = "",
        conn: Optional[Connection] = None,
    ) -> None:
        await (conn or db).execute(
            f"""
            INSERT INTO {table_with_schema(db, 'promises')}
            (amount, B_b, C_b, e, s, id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                amount,
                B_,
                C_,
                e,
                s,
                id,
            ),
        )

    async def get_promise(
        self,
        *,
        db: Database,
        B_: str,
        conn: Optional[Connection] = None,
    ) -> Optional[BlindedSignature]:
        row = await (conn or db).fetchone(
            f"""
            SELECT * from {table_with_schema(db, 'promises')}
            WHERE B_b = ?
            """,
            (str(B_),),
        )
        return BlindedSignature(amount=row[0], C_=row[2], id=row[3]) if row else None

    async def get_secrets_used(
        self,
        *,
        db: Database,
        conn: Optional[Connection] = None,
    ) -> List[str]:
        rows = await (conn or db).fetchall(f"""
            SELECT secret from {table_with_schema(db, 'proofs_used')}
            """)
        return [row[0] for row in rows]

    async def invalidate_proof(
        self,
        *,
        db: Database,
        proof: Proof,
        conn: Optional[Connection] = None,
    ) -> None:
        # we add the proof and secret to the used list
        await (conn or db).execute(
            f"""
            INSERT INTO {table_with_schema(db, 'proofs_used')}
            (amount, C, secret, id)
            VALUES (?, ?, ?, ?)
            """,
            (
                proof.amount,
                str(proof.C),
                str(proof.secret),
                str(proof.id),
            ),
        )

    async def get_proofs_pending(
        self,
        *,
        db: Database,
        conn: Optional[Connection] = None,
    ) -> List[Proof]:
        rows = await (conn or db).fetchall(f"""
            SELECT * from {table_with_schema(db, 'proofs_pending')}
            """)
        return [Proof(**r) for r in rows]

    async def set_proof_pending(
        self,
        *,
        db: Database,
        proof: Proof,
        conn: Optional[Connection] = None,
    ) -> None:
        # we add the proof and secret to the used list
        await (conn or db).execute(
            f"""
            INSERT INTO {table_with_schema(db, 'proofs_pending')}
            (amount, C, secret)
            VALUES (?, ?, ?)
            """,
            (
                proof.amount,
                str(proof.C),
                str(proof.secret),
            ),
        )

    async def unset_proof_pending(
        self,
        *,
        proof: Proof,
        db: Database,
        conn: Optional[Connection] = None,
    ):
        await (conn or db).execute(
            f"""
            DELETE FROM {table_with_schema(db, 'proofs_pending')}
            WHERE secret = ?
            """,
            (str(proof["secret"]),),
        )

    async def store_lightning_invoice(
        self,
        *,
        db: Database,
        invoice: Invoice,
        conn: Optional[Connection] = None,
    ) -> None:
        await (conn or db).execute(
            f"""
            INSERT INTO {table_with_schema(db, 'invoices')}
            (amount, pr, hash, issued, payment_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                invoice.amount,
                invoice.pr,
                invoice.hash,
                invoice.issued,
                invoice.payment_hash,
            ),
        )

    async def get_lightning_invoice(
        self,
        *,
        db: Database,
        hash: str,
        conn: Optional[Connection] = None,
    ):
        row = await (conn or db).fetchone(
            f"""
            SELECT * from {table_with_schema(db, 'invoices')}
            WHERE hash = ?
            """,
            (hash,),
        )

        return Invoice(**row) if row else None

    async def update_lightning_invoice(
        self,
        *,
        db: Database,
        hash: str,
        issued: bool,
        conn: Optional[Connection] = None,
    ) -> None:
        await (conn or db).execute(
            f"UPDATE {table_with_schema(db, 'invoices')} SET issued = ? WHERE hash = ?",
            (
                issued,
                hash,
            ),
        )

    async def store_keyset(
        self,
        *,
        db: Database,
        keyset: MintKeyset,
        conn: Optional[Connection] = None,
    ) -> None:
        await (conn or db).execute(  # type: ignore
            f"""
            INSERT INTO {table_with_schema(db, 'keysets')}
            (id, derivation_path, valid_from, valid_to, first_seen, active, version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                keyset.id,
                keyset.derivation_path,
                keyset.valid_from or db.timestamp_now,
                keyset.valid_to or db.timestamp_now,
                keyset.first_seen or db.timestamp_now,
                True,
                keyset.version,
            ),
        )

    async def get_keyset(
        self,
        *,
        db: Database,
        id: str = "",
        derivation_path: str = "",
        conn: Optional[Connection] = None,
    ) -> List[MintKeyset]:
        clauses = []
        values: List[Any] = []
        clauses.append("active = ?")
        values.append(True)
        if id:
            clauses.append("id = ?")
            values.append(id)
        if derivation_path:
            clauses.append("derivation_path = ?")
            values.append(derivation_path)
        where = ""
        if clauses:
            where = f"WHERE {' AND '.join(clauses)}"

        rows = await (conn or db).fetchall(  # type: ignore
            f"""
            SELECT * from {table_with_schema(db, 'keysets')}
            {where}
            """,
            tuple(values),
        )
        return [MintKeyset(**row) for row in rows]
