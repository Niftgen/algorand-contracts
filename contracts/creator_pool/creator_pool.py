from pyteal import *
from contracts.constants import (
    ADMIN_ID,
    ROLE,
    ADMIN_ROLE,
    SUBSCRIPTION_MODULE,
    VERIFIED_STATUS,
    STATUS,
    VERIFIED_CREATORS,
    ALGO_BALANCE,
    WITHDRAW_ASSET_COUNTER,
    WITHDRAW_ALGO_COUNTER,
)
from contracts.utility import (
    inner_asset_transaction,
    inner_payment_transaction,
    set_admin_local_txn,
)
from contracts.checkers import (
    asset_optin_checker,
    increase_pool_rewards_checker,
    increase_asset_pool_rewards_checker,
    calculate_asset_rewards_checkers,
    calculate_algo_rewards_checkers,
    withdraw_asset_reward_checkers,
    withdraw_algo_reward_checkers,
)


@Subroutine(TealType.uint64)
def deploy_contract():
    _admin_id = Txn.applications[1]

    return Seq(App.globalPut(ADMIN_ID, _admin_id), Return(Int(1)))


@Subroutine(TealType.uint64)
def asset_optin():
    _sender = Txn.sender()
    _asset_id = Txn.assets[0]

    admin_id = App.globalGet(ADMIN_ID)
    application_address = Global.current_application_address()
    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        inner_asset_transaction(application_address, _asset_id, Int(0)),
        App.globalPut(Itob(_asset_id), Int(0)),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def increase_asset_pool_rewards():
    _caller_id = Global.caller_app_id()
    _asset_id = Gtxn[0].xfer_asset()
    _asset_amount = Gtxn[0].asset_amount()

    admin_id = App.globalGet(ADMIN_ID)
    asset_balance = App.globalGet(Itob(_asset_id))

    caller_creator = AppParam.creator(_caller_id)
    subscription_module_id = App.globalGetEx(admin_id, SUBSCRIPTION_MODULE)

    return Seq(
        caller_creator,
        subscription_module_id,
        Assert(Neq(_caller_id, Int(0))),
        check_subscription_id(caller_creator.value(), subscription_module_id.value()),
        App.globalPut(Itob(_asset_id), Add(asset_balance, _asset_amount)),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def increase_pool_rewards():
    _caller_id = Global.caller_app_id()
    _amount = Gtxn[0].amount()

    admin_id = App.globalGet(ADMIN_ID)
    algo_balance = App.globalGet(ALGO_BALANCE)

    caller_creator = AppParam.creator(_caller_id)
    subscription_module_id = App.globalGetEx(admin_id, SUBSCRIPTION_MODULE)

    return Seq(
        caller_creator,
        subscription_module_id,
        Assert(Neq(_caller_id, Int(0))),
        check_subscription_id(caller_creator.value(), subscription_module_id.value()),
        App.globalPut(ALGO_BALANCE, Add(algo_balance, _amount)),
        Return(Int(1)),
    )


@Subroutine(TealType.none)
def check_subscription_id(subscription_creator_address, subscription_id):
    subscription_module_address = AppParam.address(subscription_id)

    return Seq(
        subscription_module_address,
        Assert(Eq(subscription_creator_address, subscription_module_address.value())),
    )


@Subroutine(TealType.uint64)
def calculate_asset_rewards():
    _sender = Txn.sender()
    _asset_id = Txn.assets[0]

    admin_id = App.globalGet(ADMIN_ID)
    asset_amount = App.globalGet(Itob(_asset_id))
    withdraw_asset_counter = App.globalGet(
        Concat(WITHDRAW_ASSET_COUNTER, Itob(_asset_id))
    )

    user_role = App.localGetEx(_sender, admin_id, ROLE)
    verified_creators = App.globalGetEx(admin_id, VERIFIED_CREATORS)

    return Seq(
        user_role,
        verified_creators,
        Assert(Eq(ADMIN_ROLE, user_role.value())),
        App.globalPut(
            Concat(Bytes("AMOUNT_"), Itob(_asset_id)),
            _calculate_amount(verified_creators.value(), asset_amount),
        ),
        App.globalPut(WITHDRAW_ASSET_COUNTER, Add(withdraw_asset_counter, Int(1))),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def calculate_algo_rewards():
    _sender = Txn.sender()

    admin_id = App.globalGet(ADMIN_ID)
    algo_balance = App.globalGet(ALGO_BALANCE)
    withdraw_algo_counter = App.globalGet(WITHDRAW_ALGO_COUNTER)

    user_role = App.localGetEx(_sender, admin_id, ROLE)
    verified_creators = App.globalGetEx(admin_id, VERIFIED_CREATORS)

    return Seq(
        user_role,
        verified_creators,
        Assert(Eq(ADMIN_ROLE, user_role.value())),
        App.globalPut(
            Bytes("AMOUNT_ALGO"),
            _calculate_amount(verified_creators.value(), algo_balance),
        ),
        App.globalPut(WITHDRAW_ALGO_COUNTER, Add(withdraw_algo_counter, Int(1))),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def _calculate_amount(verified_users, amount):
    amount_per_each_user = Div(amount, verified_users)

    return amount_per_each_user


@Subroutine(TealType.uint64)
def withdraw_asset_reward():
    _sender = Txn.sender()
    _asset_id = Txn.assets[0]

    asset_amount = App.globalGet(Concat(Bytes("AMOUNT_"), Itob(_asset_id)))
    withdraw_asset_counter = App.globalGet(
        Concat(WITHDRAW_ASSET_COUNTER, Itob(_asset_id))
    )

    admin_id = App.globalGet(ADMIN_ID)
    user_status = App.localGetEx(_sender, admin_id, STATUS)
    user_asset_counter = App.localGetEx(
        _sender, admin_id, Concat(WITHDRAW_ASSET_COUNTER, Itob(_asset_id))
    )

    return Seq(
        user_status,
        user_asset_counter,
        Assert(Eq(user_status.value(), VERIFIED_STATUS)),
        Assert(Neq(user_asset_counter.value(), withdraw_asset_counter)),
        inner_asset_transaction(_sender, _asset_id, asset_amount),
        set_admin_local_txn(
            _sender,
            Concat(WITHDRAW_ASSET_COUNTER, Itob(_asset_id)),
            Itob(Add(user_asset_counter.value(), Int(1))),
            Int(1),
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def withdraw_reward():
    _sender = Txn.sender()

    algo_amount = App.globalGet(Bytes("AMOUNT_ALGO"))
    withdraw_algo_counter = App.globalGet(WITHDRAW_ALGO_COUNTER)

    admin_id = App.globalGet(ADMIN_ID)
    user_status = App.localGetEx(_sender, admin_id, STATUS)
    user_algo_counter = App.localGetEx(_sender, admin_id, WITHDRAW_ALGO_COUNTER)

    return Seq(
        user_status,
        user_algo_counter,
        Assert(Eq(user_status.value(), VERIFIED_STATUS)),
        Assert(Neq(user_algo_counter.value(), withdraw_algo_counter)),
        inner_payment_transaction(_sender, algo_amount),
        set_admin_local_txn(
            _sender,
            WITHDRAW_ALGO_COUNTER,
            Itob(Add(user_algo_counter.value(), Int(1))),
            Itob(Int(1)),
        ),
        Return(Int(1)),
    )


def creator_pool_approval():
    handle_noop = Cond(
        # * Group txns === 1
        [withdraw_algo_reward_checkers(), Return(withdraw_reward())],
        [withdraw_asset_reward_checkers(), Return(withdraw_asset_reward())],
        [calculate_algo_rewards_checkers(), Return(calculate_algo_rewards())],
        [calculate_asset_rewards_checkers(), Return(calculate_asset_rewards())],
        # * Group txns > 1
        [asset_optin_checker(), Return(asset_optin())],
        [increase_pool_rewards_checker(), Return(increase_pool_rewards())],
        [increase_asset_pool_rewards_checker(), Return(increase_asset_pool_rewards())],
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
    )

    return compileTeal(program, Mode.Application, version=6)


def creator_pool_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
