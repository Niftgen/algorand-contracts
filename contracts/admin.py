from pyteal import *
from contracts.checkers import (
    set_verified_status_checker,
    assets_optin_checker,
    set_role_checker,
    add_module_checker,
    remove_module_checker,
    withdraw_algos_checker,
    withdraw_tokens_checker,
    set_local_checker,
)
from contracts.constants import (
    NFT_ID,
    PLATFORM_FEE,
    FIRST_ADMIN,
    ROLE,
    ADMIN_ROLE,
    USER_ROLE,
    VERIFIED_STATUS,
    NOT_VERIFIED_STATUS,
    STATUS,
    USDC_ASSET_ID,
    VERIFIED_CREATORS,
    NIFTGEN_ASSET,
    OWNER,
)
from contracts.utility import (
    inner_asset_transaction,
    inner_payment_transaction,
    _check_owner_role,
)


@Subroutine(TealType.none)
def rekey_to():
    return Assert(Eq(Txn.rekey_to(), Global.zero_address()))


@Subroutine(TealType.uint64)
def deploy_contract():
    _sender = Txn.sender()
    _platform_fee = Btoi(Txn.application_args[0])
    _first_admin = Txn.accounts[1]
    _niftgen_asset_id = Txn.assets[0]
    _usdc_asset_id = Txn.assets[1]

    return Seq(
        App.globalPut(PLATFORM_FEE, _platform_fee),
        App.globalPut(OWNER, _sender),
        App.globalPut(FIRST_ADMIN, _first_admin),
        App.globalPut(NIFTGEN_ASSET, _niftgen_asset_id),
        App.globalPut(USDC_ASSET_ID, _usdc_asset_id),
        App.globalPut(VERIFIED_CREATORS, Int(0)),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def change_ownership():
    _sender = Txn.sender()
    _new_owner = Txn.accounts[1]

    owner = App.globalGet(OWNER)

    return Seq(
        Assert(Eq(_sender, owner)),
        Assert(Neq(_sender, _new_owner)),
        App.globalPut(OWNER, _new_owner),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def assets_optin():
    _sender = Txn.sender()
    _niftgen_asset = Txn.assets[0]
    _usdc_asset = Txn.assets[1]
    sender_role = App.localGet(_sender, ROLE)

    niftgen_asset_id = App.globalGet(NIFTGEN_ASSET)
    usdc_asset_id = App.globalGet(USDC_ASSET_ID)

    return Seq(
        Assert(Eq(sender_role, Int(1))),
        Assert(Eq(_usdc_asset, usdc_asset_id)),
        Assert(Eq(_niftgen_asset, niftgen_asset_id)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.asset_amount: Int(0),
                TxnField.xfer_asset: _niftgen_asset,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.asset_amount: Int(0),
                TxnField.xfer_asset: _usdc_asset,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def optin_admin():
    _sender = Txn.sender()
    first_admin = App.globalGet(FIRST_ADMIN)
    owner = App.globalGet(OWNER)

    return Seq(
        rekey_to(),
        If(Eq(_sender, first_admin))
        .Then(
            Seq(
                App.localPut(_sender, ROLE, ADMIN_ROLE),
                App.globalPut(FIRST_ADMIN, Global.zero_address()),
            )
        )
        .Else(
            If(Eq(_sender, owner))
            .Then(
                App.localPut(_sender, ROLE, ADMIN_ROLE),
            )
            .Else(
                App.localPut(_sender, ROLE, USER_ROLE),
            ),
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def set_role():
    _sender = Txn.sender()
    _account_to_set = Txn.accounts[1]
    _role = Btoi(Txn.application_args[1])

    return Seq(
        If(Neq(_sender, App.globalGet(OWNER))).Then(
            Assert(Eq(App.localGet(_sender, ROLE), ADMIN_ROLE)),
        ),
        Assert(Neq(_sender, _account_to_set)),
        Assert(Or(Eq(_role, USER_ROLE), Eq(_role, ADMIN_ROLE))),
        App.localPut(_account_to_set, ROLE, _role),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def add_module():
    _sender = Txn.sender()
    _module_name = Txn.application_args[1]
    _module_id = Txn.applications[1]

    role = App.localGet(_sender, ROLE)

    return Seq(
        Assert(Eq(role, ADMIN_ROLE)),
        App.globalPut(_module_name, _module_id),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def remove_module():
    _sender = Txn.sender()
    role = App.localGet(_sender, ROLE)
    _module_name = Txn.application_args[1]
    module = App.globalGet(_module_name)

    return Seq(
        Assert(Eq(role, ADMIN_ROLE)),
        App.globalDel(module),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def withdraw_algos():
    _sender = Txn.sender()
    _beneficiary = Txn.accounts[1]
    _amount = Btoi(Txn.application_args[1])

    is_owner = App.globalGet(OWNER)

    return Seq(
        Assert(Eq(is_owner, _sender)),
        inner_payment_transaction(_beneficiary, _amount),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def withdraw_tokens():
    _sender = Txn.sender()
    _beneficiary = Txn.accounts[1]
    _amount = Btoi(Txn.application_args[1])
    _asset_id = Txn.assets[0]

    is_owner = App.globalGet(OWNER)

    return Seq(
        Assert(Eq(is_owner, _sender)),
        inner_asset_transaction(_beneficiary, _asset_id, _amount),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def update_app():

    return Seq(_check_owner_role(), Return(Int(1)))


@Subroutine(TealType.uint64)
def set_verified_status():
    _sender = Txn.sender()
    _account_to_set = Txn.accounts[1]
    _new_status = Btoi(Txn.application_args[1])

    verified_creators = App.globalGet(VERIFIED_CREATORS)
    sender_role = App.localGet(_sender, ROLE)

    return Seq(
        Assert(Eq(sender_role, ADMIN_ROLE)),
        Assert(Neq(_sender, _account_to_set)),
        Assert(
            Or(Eq(_new_status, VERIFIED_STATUS), Eq(_new_status, NOT_VERIFIED_STATUS))
        ),
        App.localPut(_account_to_set, STATUS, _new_status),
        If(Eq(_new_status, VERIFIED_STATUS))
        .Then(App.globalPut(VERIFIED_CREATORS, Add(verified_creators, Int(1))))
        .Else(App.globalPut(VERIFIED_CREATORS, Minus(verified_creators, Int(1)))),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def set_local():
    _sender_id = Global.caller_app_id()
    _beneficiary = Txn.accounts[1]
    _module_name = Txn.application_args[1]
    _local_name = Txn.application_args[2]
    _local_value = Txn.application_args[3]
    _local_int = Btoi(Txn.application_args[4])

    module_id = App.globalGet(_module_name)

    return Seq(
        Assert(Neq(_sender_id, Int(0))),
        Assert(Eq(_sender_id, module_id)),
        # * If the global_int is 0 the value is in bytes otherwise is a number
        If(Eq(_local_int, Int(0)))
        .Then(
            App.localPut(_beneficiary, _local_name, _local_value),
        )
        .Else(
            App.localPut(_beneficiary, _local_name, Btoi(_local_value)),
        ),
        Return(Int(1)),
    )


def admin_approval():
    handle_noop = Cond(
        # * GROUP SIZE = 1
        [
            set_local_checker(),
            Return(change_ownership()),
        ],
        [
            set_local_checker(),
            Return(set_local()),
        ],
        [withdraw_algos_checker(), Return(withdraw_algos())],
        [withdraw_tokens_checker(), Return(withdraw_tokens())],
        [
            set_role_checker(),
            Return(set_role()),
        ],
        [
            set_verified_status_checker(),
            Return(set_verified_status()),
        ],
        [
            add_module_checker(),
            Return(add_module()),
        ],
        [
            remove_module_checker(),
            Return(remove_module()),
        ],
        # * GROUP SIZE > 1
        [
            assets_optin_checker(),
            Return(assets_optin()),
        ],
    )

    program = Cond(
        [Txn.application_id() == Int(0), Return(deploy_contract())],
        [
            Txn.on_completion() == OnComplete.OptIn,
            Return(optin_admin()),
        ],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(update_app())],
    )

    return compileTeal(program, Mode.Application, version=6)


def admin_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
