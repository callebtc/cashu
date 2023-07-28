import pytest

from cashu.core.base import TokenV3
from cashu.core.helpers import calculate_number_of_blank_outputs
from cashu.core.split import amount_split


def test_get_output_split():
    assert amount_split(13) == [1, 4, 8]


def test_tokenv3_get_amount():
    token_str = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIkplaFpMVTZuQ3BSZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogIjBFN2lDazRkVmxSZjVQRjFnNFpWMnci"
        "LCAiQyI6ICIwM2FiNTgwYWQ5NTc3OGVkNTI5NmY4YmVlNjU1ZGJkN2Q2NDJmNWQzMmRlOGUyNDg0NzdlMGI0ZDZhYTg2M2ZjZDUifSwgeyJpZCI6ICJKZWhaTFU2bkNwUmQiLCAiYW"
        "1vdW50IjogOCwgInNlY3JldCI6ICJzNklwZXh3SGNxcXVLZDZYbW9qTDJnIiwgIkMiOiAiMDIyZDAwNGY5ZWMxNmE1OGFkOTAxNGMyNTliNmQ2MTRlZDM2ODgyOWYwMmMzODc3M2M0"
        "NzIyMWY0OTYxY2UzZjIzIn1dLCAibWludCI6ICJodHRwOi8vbG9jYWxob3N0OjMzMzgifV19"
    )
    token = TokenV3.deserialize(token_str)
    assert token.get_amount() == 10


def test_tokenv3_get_proofs():
    token_str = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIkplaFpMVTZuQ3BSZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogIjBFN2lDazRkVmxSZjVQRjFnNFpWMnci"
        "LCAiQyI6ICIwM2FiNTgwYWQ5NTc3OGVkNTI5NmY4YmVlNjU1ZGJkN2Q2NDJmNWQzMmRlOGUyNDg0NzdlMGI0ZDZhYTg2M2ZjZDUifSwgeyJpZCI6ICJKZWhaTFU2bkNwUmQiLCAiYW"
        "1vdW50IjogOCwgInNlY3JldCI6ICJzNklwZXh3SGNxcXVLZDZYbW9qTDJnIiwgIkMiOiAiMDIyZDAwNGY5ZWMxNmE1OGFkOTAxNGMyNTliNmQ2MTRlZDM2ODgyOWYwMmMzODc3M2M0"
        "NzIyMWY0OTYxY2UzZjIzIn1dLCAibWludCI6ICJodHRwOi8vbG9jYWxob3N0OjMzMzgifV19"
    )
    token = TokenV3.deserialize(token_str)
    assert len(token.get_proofs()) == 2


def test_tokenv3_deserialize_serialize_with_dleq():
    token_str = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIjI4ajhueVNMMU5kZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogInFvS01lMGk1LVgyQy0zc29mVUZUb0Ei"
        "LCAiQyI6ICIwMmIzYWVlMjAxZDRmYzlhODJkYTJiZTVmOTQzODlmOWIxMzg4YzBkMDA3N2M2ODg1MDhjODIzZmU4OTMwY2YwYzYiLCAiZGxlcSI6IHsiZSI6ICJjMmJkNTM"
        "zMTkyZDI2MzExMzM2MjU1OTUxZmQyZTI2OWEwY2E2ODViMzgxMDcwYTFhMzRiMDViYjVlYTBkNTAzIiwgInMiOiAiNzUxOTc5MDczZjk3YjcyMmYzNzJkMzRjZDhlNmY5MWR"
        "lYzA0ODE4MTg5NjI3YjYwZWFmYjZjMTY3MjFiZjVmOCIsICJCXyI6ICIwMjVhZjliM2ViNmFkZjgxN2M0YzBjMzhhYWYwZjNhYmJjY2MxODFhY2VmMmNjZTQ4Mzg3MWIwYzE"
        "yM2UwOTI1NDgiLCAiQ18iOiAiMDNlMDA2YTRiNGI1ODNlMzI5NTNmYzFmMWI4MmQyZTE1MmQyMjdlYTFhZTgyZTEyOWNiYzc3OWQ5NzYwMTc1Mzg4In19LCB7ImlkIjogIjI4"
        "ajhueVNMMU5kZCIsICJhbW91bnQiOiA4LCAic2VjcmV0IjogIk1TcEdMMG9Qc3cyU2dFOTdvNmh3emciLCAiQyI6ICIwM2EyYjJmMTBjOGI2MjQ0ODRhYmNmYTc3MzUwYjhiN"
        "WU1NDAwZWFhYmQxNjA0ZTRjYjliYWQyNjJkZmFhOThmYTgiLCAiZGxlcSI6IHsiZSI6ICJkODI0YzRjNGExNTBmZTQxM2JjM2YzOGNkMGE2NjAxZDU1NWVhYzhjOTNmNDMyOT"
        "c0NzQxMGEwOGMzZmYyNTg4IiwgInMiOiAiMjZkZjdhZTk4NzdjN2YyZTE2N2FkZGI4MWRkYjFlNjg1NTE5NmY1NDE3ZDI3MDFiYTdkZmM0NDlkNjYwNTQyZiIsICJCXyI6ICI"
        "wMmJlNzQ0NzllOTM0NWU3NWRhNWUzYzliYzcxYjBhMTZlNzZhNDJkMDVjMDA3M2ZjYjgzZmNlYTg3YWJmZGFhYTciLCAiQ18iOiAiMDNkYjA3MjdjYWNjMTQwYTljMzg0YjQx"
        "ZjJhMjUyYTg3ODI5YWZhMWU4OWJjZTFlMGY4YWQyMGJkNGQ5Zjc4YjgyIn19XSwgIm1pbnQiOiAiaHR0cDovL2xvY2FsaG9zdDozMzM4In1dfQ=="
    )
    token = TokenV3.deserialize(token_str)
    assert token.serialize(include_dleq=True) == token_str


def test_tokenv3_deserialize_serialize():
    token_str = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIkplaFpMVTZuQ3BSZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogIjBFN2lDazRkVmxSZjVQRjFnNFpWMnci"
        "LCAiQyI6ICIwM2FiNTgwYWQ5NTc3OGVkNTI5NmY4YmVlNjU1ZGJkN2Q2NDJmNWQzMmRlOGUyNDg0NzdlMGI0ZDZhYTg2M2ZjZDUifSwgeyJpZCI6ICJKZWhaTFU2bkNwUmQiLCAiYW"
        "1vdW50IjogOCwgInNlY3JldCI6ICJzNklwZXh3SGNxcXVLZDZYbW9qTDJnIiwgIkMiOiAiMDIyZDAwNGY5ZWMxNmE1OGFkOTAxNGMyNTliNmQ2MTRlZDM2ODgyOWYwMmMzODc3M2M0"
        "NzIyMWY0OTYxY2UzZjIzIn1dLCAibWludCI6ICJodHRwOi8vbG9jYWxob3N0OjMzMzgifV19"
    )
    token = TokenV3.deserialize(token_str)
    assert token.serialize() == token_str


def test_tokenv3_deserialize_serialize_no_dleq():
    token_str = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIjI4ajhueVNMMU5kZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogInFvS01lMGk1LVgyQy0zc29mV"
        "UZUb0EiLCAiQyI6ICIwMmIzYWVlMjAxZDRmYzlhODJkYTJiZTVmOTQzODlmOWIxMzg4YzBkMDA3N2M2ODg1MDhjODIzZmU4OTMwY2YwYzYiLCAiZGxlcSI6IHsiZ"
        "SI6ICJjMmJkNTMzMTkyZDI2MzExMzM2MjU1OTUxZmQyZTI2OWEwY2E2ODViMzgxMDcwYTFhMzRiMDViYjVlYTBkNTAzIiwgInMiOiAiNzUxOTc5MDczZjk3YjcyM"
        "mYzNzJkMzRjZDhlNmY5MWRlYzA0ODE4MTg5NjI3YjYwZWFmYjZjMTY3MjFiZjVmOCIsICJCXyI6ICIwMjVhZjliM2ViNmFkZjgxN2M0YzBjMzhhYWYwZjNhYmJjY"
        "2MxODFhY2VmMmNjZTQ4Mzg3MWIwYzEyM2UwOTI1NDgiLCAiQ18iOiAiMDNlMDA2YTRiNGI1ODNlMzI5NTNmYzFmMWI4MmQyZTE1MmQyMjdlYTFhZTgyZTEyOWNiY"
        "zc3OWQ5NzYwMTc1Mzg4In19LCB7ImlkIjogIjI4ajhueVNMMU5kZCIsICJhbW91bnQiOiA4LCAic2VjcmV0IjogIk1TcEdMMG9Qc3cyU2dFOTdvNmh3emciLCAiQ"
        "yI6ICIwM2EyYjJmMTBjOGI2MjQ0ODRhYmNmYTc3MzUwYjhiNWU1NDAwZWFhYmQxNjA0ZTRjYjliYWQyNjJkZmFhOThmYTgiLCAiZGxlcSI6IHsiZSI6ICJkODI0Y"
        "zRjNGExNTBmZTQxM2JjM2YzOGNkMGE2NjAxZDU1NWVhYzhjOTNmNDMyOTc0NzQxMGEwOGMzZmYyNTg4IiwgInMiOiAiMjZkZjdhZTk4NzdjN2YyZTE2N2FkZGI4M"
        "WRkYjFlNjg1NTE5NmY1NDE3ZDI3MDFiYTdkZmM0NDlkNjYwNTQyZiIsICJCXyI6ICIwMmJlNzQ0NzllOTM0NWU3NWRhNWUzYzliYzcxYjBhMTZlNzZhNDJkMDVjM"
        "DA3M2ZjYjgzZmNlYTg3YWJmZGFhYTciLCAiQ18iOiAiMDNkYjA3MjdjYWNjMTQwYTljMzg0YjQxZjJhMjUyYTg3ODI5YWZhMWU4OWJjZTFlMGY4YWQyMGJkNGQ5Z"
        "jc4YjgyIn19XSwgIm1pbnQiOiAiaHR0cDovL2xvY2FsaG9zdDozMzM4In1dfQ=="
    )
    token_str_no_dleq = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIjI4ajhueVNMMU5kZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogInFvS01lMG"
        "k1LVgyQy0zc29mVUZUb0EiLCAiQyI6ICIwMmIzYWVlMjAxZDRmYzlhODJkYTJiZTVmOTQzODlmOWIxMzg4YzBkMDA3N2M2ODg1MDhjODIzZmU"
        "4OTMwY2YwYzYifSwgeyJpZCI6ICIyOGo4bnlTTDFOZGQiLCAiYW1vdW50IjogOCwgInNlY3JldCI6ICJNU3BHTDBvUHN3MlNnRTk3bzZod3pn"
        "IiwgIkMiOiAiMDNhMmIyZjEwYzhiNjI0NDg0YWJjZmE3NzM1MGI4YjVlNTQwMGVhYWJkMTYwNGU0Y2I5YmFkMjYyZGZhYTk4ZmE4In1dLCAib"
        "WludCI6ICJodHRwOi8vbG9jYWxob3N0OjMzMzgifV19"
    )
    token = TokenV3.deserialize(token_str)
    assert token.serialize(include_dleq=False) == token_str_no_dleq


def test_tokenv3_deserialize_with_memo():
    token_str = (
        "cashuAeyJ0b2tlbiI6IFt7InByb29mcyI6IFt7ImlkIjogIkplaFpMVTZuQ3BSZCIsICJhbW91bnQiOiAyLCAic2VjcmV0IjogIjBFN2lDazRkVmxSZjV"
        "QRjFnNFpWMnciLCAiQyI6ICIwM2FiNTgwYWQ5NTc3OGVkNTI5NmY4YmVlNjU1ZGJkN2Q2NDJmNWQzMmRlOGUyNDg0NzdlMGI0ZDZhYTg2M2ZjZDUifSwg"
        "eyJpZCI6ICJKZWhaTFU2bkNwUmQiLCAiYW1vdW50IjogOCwgInNlY3JldCI6ICJzNklwZXh3SGNxcXVLZDZYbW9qTDJnIiwgIkMiOiAiMDIyZDAwNGY5Z"
        "WMxNmE1OGFkOTAxNGMyNTliNmQ2MTRlZDM2ODgyOWYwMmMzODc3M2M0NzIyMWY0OTYxY2UzZjIzIn1dLCAibWludCI6ICJodHRwOi8vbG9jYWxob3N0Oj"
        "MzMzgifV0sICJtZW1vIjogIlRlc3QgbWVtbyJ9"
    )
    token = TokenV3.deserialize(token_str)
    assert token.serialize() == token_str
    assert token.memo == "Test memo"


def test_calculate_number_of_blank_outputs():
    # Example from NUT-08 specification.
    fee_reserve_sat = 1000
    expected_n_blank_outputs = 10
    n_blank_outputs = calculate_number_of_blank_outputs(fee_reserve_sat)
    assert n_blank_outputs == expected_n_blank_outputs


def test_calculate_number_of_blank_outputs_for_small_fee_reserve():
    # There should always be at least one blank output.
    fee_reserve_sat = 1
    expected_n_blank_outputs = 1
    n_blank_outputs = calculate_number_of_blank_outputs(fee_reserve_sat)
    assert n_blank_outputs == expected_n_blank_outputs


def test_calculate_number_of_blank_outputs_for_zero_fee_reserve():
    # Negative fee reserve is not supported.
    fee_reserve_sat = 0
    n_blank_outputs = calculate_number_of_blank_outputs(fee_reserve_sat)
    assert n_blank_outputs == 0


def test_calculate_number_of_blank_outputs_fails_for_negative_fee_reserve():
    # Negative fee reserve is not supported.
    fee_reserve_sat = -1
    with pytest.raises(AssertionError):
        _ = calculate_number_of_blank_outputs(fee_reserve_sat)
