from pyteal import *
from contracts.checkers import change_admin_id_checker, deploy_subscription_app_checker

from contracts.constants import (
    ADMIN_ID,
    ADMIN_ROLE,
    NEW_ADMIN_ID,
    ROLE,
    MODULE_NAME,
    SUBSCRIPTION_MODULE,
    ASSET_OPTIN,
    SUBSCRIPTION_APP_ID,
    USDC_ASSET_ID,
)
from contracts.utility import (
    _check_owner_role,
    inner_contract_payment_transaction,
)


@Subroutine(TealType.uint64)
def deploy_contract():
    _admin_id = Txn.applications[1]

    usdc_asset_id = App.globalGetEx(_admin_id, USDC_ASSET_ID)

    return Seq(
        usdc_asset_id,
        Assert(Eq(usdc_asset_id.hasValue(), Int(1))),
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(MODULE_NAME, SUBSCRIPTION_MODULE),
        App.globalPut(USDC_ASSET_ID, usdc_asset_id.value()),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def optin():
    _sender = Txn.sender()

    return Seq(
        App.localPut(_sender, SUBSCRIPTION_APP_ID, Int(0)),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def change_admin_id():
    _sender = Txn.sender()

    admin_id = App.globalGet(ADMIN_ID)
    new_admin_id = App.globalGet(NEW_ADMIN_ID)
    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        App.globalPut(ADMIN_ID, new_admin_id),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def update_app():
    return Seq(_check_owner_role(), Return(Int(1)))


@Subroutine(TealType.uint64)
def deploy_subscription_app(
    subscription_app_approval_compiled, subscription_app_clear_compiled
):
    _subscription_owner = Txn.sender()

    admin_id = App.globalGet(ADMIN_ID)
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_app_id = ScratchVar(TealType.uint64)

    return Seq(
        usdc_asset_id,
        Assert(Eq(usdc_asset_id.hasValue(), Int(1))),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.approval_program: subscription_app_approval_compiled,
                TxnField.clear_state_program: subscription_app_clear_compiled,
                TxnField.applications: [admin_id],
                TxnField.accounts: [_subscription_owner],
                TxnField.assets: [usdc_asset_id.value()],
                TxnField.fee: Int(0),
                TxnField.local_num_uints: Int(5),
                TxnField.local_num_byte_slices: Int(1),
                TxnField.global_num_uints: Int(2),
                TxnField.global_num_byte_slices: Int(2),
                TxnField.extra_program_pages: Int(1),
            }
        ),
        InnerTxnBuilder.Submit(),
        subscription_app_id.store(InnerTxn.created_application_id()),
        inner_contract_payment_transaction(subscription_app_id.load(), Int(100_000)),
        subscription_optin(subscription_app_id.load(), usdc_asset_id.value()),
        App.localPut(
            _subscription_owner, SUBSCRIPTION_APP_ID, subscription_app_id.load()
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.none)
def subscription_optin(subscription_app_id, usdc_asset_id):
    subscription_app_address = AppParam.address(subscription_app_id)

    return Seq(
        subscription_app_address,
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.receiver: subscription_app_address.value(),
                TxnField.amount: Int(100_000),
                TxnField.fee: Int(0),
                TxnField.type_enum: TxnType.Payment,
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.application_id: subscription_app_id,
                TxnField.application_args: [ASSET_OPTIN],
                TxnField.fee: Int(0),
                TxnField.assets: [usdc_asset_id],
                TxnField.type_enum: TxnType.ApplicationCall,
            }
        ),
        InnerTxnBuilder.Submit(),
    )


def subscription_module_approval(
    subscription_app_approval_compiled, subscription_app_clear_compiled
):
    handle_noop = Cond(
        # * Group transaction === 1
        [
            change_admin_id_checker(),
            Return(change_admin_id()),
        ],
        # * Group transaction > 1
        [
            deploy_subscription_app_checker(),
            Return(
                deploy_subscription_app(
                    Bytes("base64", subscription_app_approval_compiled),
                    Bytes("base64", subscription_app_clear_compiled),
                )
            ),
        ],
    )

    program = Cond(
        [
            And(
                Eq(Txn.application_id(), Int(0)),
                Eq(Global.group_size(), Int(1)),
                Eq(Txn.rekey_to(), Global.zero_address()),
            ),
            Return(deploy_contract()),
        ],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
        [Txn.on_completion() == OnComplete.OptIn, Return(optin())],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(update_app())],
    )

    return compileTeal(program, Mode.Application, version=6)


def subscription_module_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
