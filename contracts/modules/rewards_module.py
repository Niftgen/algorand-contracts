from pyteal import *
from contracts.checkers import (
    change_admin_id_checker,
    decrease_rewards_checker,
    emergency_withdraw_checker,
    get_pending_rewards_checker,
    increase_rewards_checker,
    optin_niftgen_asset_checker,
)
from contracts.constants import (
    ADMIN_ID,
    ADMIN_ROLE,
    FEES_TO_PAY,
    NEW_ADMIN_ID,
    REWARDS_AMOUNT,
    ROLE,
    MODULE_NAME,
    DAILY_DATE,
    DAILY_AMOUNT,
    REWARD_MODULE,
    NIFTGEN_ASSET,
)
from contracts.utility import (
    inner_asset_transaction,
    _check_owner_role,
    inner_freeze_subscription,
    inner_unfreeze_subscription,
)


@Subroutine(TealType.none)
def _check_daily_max(beneficiary, daily_amount, amount, daily_date):
    return Seq(
        Assert(Lt(daily_amount, Int(24_000_000))),
        Assert(Le(amount, Int(24_000_000))),
        If(Gt(Add(daily_amount, amount), Int(24_000_000)))
        .Then(
            Seq(
                If(Gt(daily_date, Global.latest_timestamp())).Then(Seq(Reject())),
                App.localPut(beneficiary, DAILY_DATE, Global.latest_timestamp()),
                App.localPut(beneficiary, DAILY_AMOUNT, amount),
            )
        )
        .Else(
            Seq(
                App.localPut(beneficiary, DAILY_AMOUNT, Add(daily_amount, amount)),
                If(Gt(Global.latest_timestamp(), daily_date)).Then(
                    Seq(
                        App.localPut(
                            beneficiary, DAILY_DATE, Global.latest_timestamp()
                        ),
                        App.localPut(beneficiary, DAILY_AMOUNT, amount),
                    )
                ),
            )
        ),
    )


@Subroutine(TealType.uint64)
def deploy_contract():
    _admin_id = Txn.applications[1]

    return Seq(
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(MODULE_NAME, REWARD_MODULE),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def optin():
    _sender = Txn.sender()

    return Seq(
        App.localPut(_sender, REWARDS_AMOUNT, Int(0)),
        App.localPut(_sender, FEES_TO_PAY, Int(0)),
        App.localPut(_sender, DAILY_AMOUNT, Int(0)),
        App.localPut(_sender, DAILY_DATE, Global.latest_timestamp()),
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
def optin_niftgen_asset():
    _sender = Txn.sender()
    _niftgen_asset = Txn.assets[0]

    admin_id = App.globalGet(ADMIN_ID)
    niftgen_asset = App.globalGetEx(admin_id, NIFTGEN_ASSET)
    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        niftgen_asset,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        Assert(Eq(niftgen_asset.value(), _niftgen_asset)),
        inner_asset_transaction(
            Global.current_application_address(), _niftgen_asset, Int(0)
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def emergency_withdraw():
    _sender = Txn.sender()
    _beneficiary = Txn.accounts[1]
    _asset_id = Txn.assets[0]

    admin_id = App.globalGet(ADMIN_ID)
    sender_role = App.localGetEx(_sender, admin_id, ROLE)
    asset_balance = AssetHolding.balance(
        Global.current_application_address(), _asset_id
    )

    return Seq(
        sender_role,
        asset_balance,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        inner_asset_transaction(_beneficiary, _asset_id, asset_balance.value()),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def increase_rewards():
    _sender = Txn.sender()
    _beneficiary = Txn.accounts[1]
    _amount = Btoi(Txn.application_args[1])

    admin_id = App.globalGet(ADMIN_ID)
    rewards_amount = App.localGet(_beneficiary, REWARDS_AMOUNT)
    fees_to_pay = App.localGet(_beneficiary, FEES_TO_PAY)
    daily_amount = App.localGet(_beneficiary, DAILY_AMOUNT)
    daily_date = App.localGet(_beneficiary, DAILY_DATE)
    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        _check_daily_max(_beneficiary, daily_amount, _amount, daily_date),
        App.localPut(_beneficiary, REWARDS_AMOUNT, Add(rewards_amount, _amount)),
        App.localPut(_beneficiary, FEES_TO_PAY, Add(fees_to_pay, Int(1000))),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def decrease_rewards():
    _sender = Txn.sender()
    _beneficiary = Txn.accounts[1]
    _amount = Btoi(Txn.application_args[1])

    admin_id = App.globalGet(ADMIN_ID)
    rewards_amount = App.localGet(_beneficiary, REWARDS_AMOUNT)
    fees_to_pay = App.localGet(_beneficiary, FEES_TO_PAY)
    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        App.localPut(_beneficiary, REWARDS_AMOUNT, Minus(rewards_amount, _amount)),
        App.localPut(_beneficiary, FEES_TO_PAY, Add(fees_to_pay, Int(1000))),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def get_pending_rewards():
    _sender = Txn.sender()
    _amount = Btoi(Txn.application_args[1])
    _asset_id = Txn.assets[0]

    rewards_amount = App.localGet(_sender, REWARDS_AMOUNT)
    fees_to_pay = App.localGet(_sender, FEES_TO_PAY)
    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)

    is_frozen_address = AssetHolding.frozen(_sender, _asset_id)

    return Seq(
        admin_address,
        is_frozen_address,
        If(Eq(is_frozen_address.value(), Int(1))).Then(
            inner_unfreeze_subscription(_sender, _asset_id)
        ),
        Assert(Le(_amount, rewards_amount)),
        Assert(Eq(Gtxn[0].amount(), fees_to_pay)),
        Assert(Eq(Gtxn[0].receiver(), admin_address.value())),
        inner_asset_transaction(_sender, _asset_id, _amount),
        App.localPut(_sender, REWARDS_AMOUNT, Minus(rewards_amount, _amount)),
        App.localPut(_sender, FEES_TO_PAY, Int(0)),
        inner_freeze_subscription(_sender, _asset_id),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def update_app():

    return Seq(_check_owner_role(), Return(Int(1)))


def rewards_module_approval():
    handle_noop = Cond(
        # * Group transaction === 1
        [
            change_admin_id_checker(),
            Return(change_admin_id()),
        ],
        [
            emergency_withdraw_checker(),
            Return(emergency_withdraw()),
        ],
        [
            increase_rewards_checker(),
            Return(increase_rewards()),
        ],
        [
            decrease_rewards_checker(),
            Return(decrease_rewards()),
        ],
        [
            get_pending_rewards_checker(),
            Return(get_pending_rewards()),
        ],
        # * Group transaction >= 1
        [optin_niftgen_asset_checker(), Return(optin_niftgen_asset())],
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


def rewards_module_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
