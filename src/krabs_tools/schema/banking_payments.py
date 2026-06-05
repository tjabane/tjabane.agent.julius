from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TransferInstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    beneficiary_account_id: str = Field(alias="beneficiaryAccountId", min_length=1)
    amount: float = Field(gt=0)
    my_reference: str = Field(alias="myReference", min_length=1)
    their_reference: str = Field(alias="theirReference", min_length=1)


class BeneficiaryPaymentInstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    beneficiary_id: str = Field(alias="beneficiaryId", min_length=1)
    amount: float = Field(gt=0)
    my_reference: str = Field(alias="myReference", min_length=1)
    their_reference: str = Field(alias="theirReference", min_length=1)


class TransferFundsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    transfers: list[TransferInstruction] = Field(min_length=1)
    profile_id: str | None = None

    def to_transfer_dicts(self) -> list[dict[str, Any]]:
        return [transfer.model_dump(by_alias=True) for transfer in self.transfers]


class GetBeneficiariesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetBeneficiaryCategoriesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PayBeneficiariesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    payments: list[BeneficiaryPaymentInstruction] = Field(min_length=1)

    def to_payment_dicts(self) -> list[dict[str, Any]]:
        return [payment.model_dump(by_alias=True) for payment in self.payments]
