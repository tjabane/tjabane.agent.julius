from typing import Any

from krabs_domain.contracts import BankingClient
from krabs_tools.schema.banking_payments import (
    GetBeneficiariesInput,
    GetBeneficiaryCategoriesInput,
    PayBeneficiariesInput,
    TransferFundsInput,
)


class TransferFundsTool:
    name = "transfer_funds"
    description = "Transfer funds from a bank account. Only call this after the user has explicitly confirmed the exact transfer details."
    input_schema = TransferFundsInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: TransferFundsInput) -> list[dict[str, Any]]:
        return self._banking_client.transfer_funds(
            account_id=input_data.account_id,
            transfers=input_data.to_transfer_dicts(),
            profile_id=input_data.profile_id,
        )


class GetBeneficiariesTool:
    name = "get_beneficiaries"
    description = "Get a list of bank beneficiaries available to the authenticated user."
    input_schema = GetBeneficiariesInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetBeneficiariesInput) -> list[dict[str, Any]]:
        _ = input_data
        return self._banking_client.get_beneficiaries()


class GetBeneficiaryCategoriesTool:
    name = "get_beneficiary_categories"
    description = "Get bank beneficiary categories available to the authenticated user."
    input_schema = GetBeneficiaryCategoriesInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetBeneficiaryCategoriesInput) -> list[dict[str, Any]]:
        _ = input_data
        return self._banking_client.get_beneficiary_categories()


class PayBeneficiariesTool:
    name = "pay_beneficiaries"
    description = "Pay one or more bank beneficiaries from an account. Only call this after the user has explicitly confirmed the exact payment details."
    input_schema = PayBeneficiariesInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: PayBeneficiariesInput) -> list[dict[str, Any]]:
        return self._banking_client.pay_beneficiaries(
            account_id=input_data.account_id,
            payments=input_data.to_payment_dicts(),
        )
