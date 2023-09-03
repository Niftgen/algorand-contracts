from pyteal import *
from contracts.checkers import (
    change_admin_id_checker,
    asset_optin_checker,
    subscribe_checker,
    utility_checker,
    renew_checker,
)
from contracts.constants import *
from contracts.utility import (
    _check_owner_role,
    _check_admin_role,
    inner_asset_transaction,
    inner_payment_transaction,
    increase_algo_pool_creator,
    increase_asset_pool_creator,
)


@Subroutine(TealType.uint64)
def deploy_contract():
    _admin_id = Txn.applications[1]
    _creator_address = Txn.accounts[1]
    _usdc = Txn.assets[0]

    return Seq(
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(MODULE_NAME, SUBSCRIPTION_APP),
        App.globalPut(CREATOR_ADDRESS, _creator_address),
        App.globalPut(USDC_ASSET_ID, _usdc),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def usdc_asset_optin():
    _sender = Txn.sender()

    usdc_asset_id = App.globalGet(USDC_ASSET_ID)
    creator_address = Global.creator_address()

    return Seq(
        Assert(Eq(_sender, creator_address)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.asset_amount: Int(0),
                TxnField.xfer_asset: usdc_asset_id,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
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
def optin():
    _sender = Txn.sender()

    creator_address = App.globalGet(CREATOR_ADDRESS)

    return Seq(
        App.localPut(_sender, SUBSCRIPTION_STATUS, BASIC_SUBSCRIPTION),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, Int(0)),
        App.localPut(_sender, CREATOR_ADDRESS, creator_address),
        Return(Int(1)),
    )


@Subroutine(TealType.none)
def subscribe_creator():
    _sender = Txn.sender()
    _admin = Gtxn[2].sender()
    _payment_type = Btoi(Gtxn[2].application_args[1])
    _amount_to_receive = Btoi(Gtxn[2].application_args[2])
    _new_expires_date = Btoi(Gtxn[2].application_args[3])
    _creator_pool_address = Gtxn[2].accounts[1]

    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)
    app_address = Global.current_application_address()
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_status = App.localGet(_sender, SUBSCRIPTION_STATUS)

    timestamp = Global.latest_timestamp()
    expires_date = App.localGet(_sender, SUBSCRIPTION_EXPIRES_DATE)
    amount_to_admin_fee = WideRatio([_amount_to_receive, Int(30)], [Int(100)])
    amount_to_creator = WideRatio([_amount_to_receive, Int(70)], [Int(100)])

    return Seq(
        usdc_asset_id,
        admin_address,
        _check_admin_role(_admin),
        Assert(Eq(subscription_status, BASIC_SUBSCRIPTION)),
        Assert(Ge(timestamp, expires_date)),
        Assert(Gt(_new_expires_date, Global.latest_timestamp())),
        Assert(Or(Eq(_payment_type, ALGO), Eq(_payment_type, USDC))),
        If(Eq(_payment_type, ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                Assert(Eq(Gtxn[0].amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].receiver(), app_address)),
                Assert(Eq(Gtxn[0].sender(), _sender)),
                inner_payment_transaction(admin_address.value(), amount_to_admin_fee),
                inner_payment_transaction(_creator_pool_address, amount_to_creator),
            )
        ),
        If(Eq(_payment_type, USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset_id.value())),
                Assert(Eq(Gtxn[0].asset_amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].asset_receiver(), app_address)),
                Assert(Eq(Gtxn[0].asset_sender(), _sender)),
                inner_asset_transaction(
                    admin_address.value(), usdc_asset_id.value(), amount_to_admin_fee
                ),
                inner_asset_transaction(
                    _creator_pool_address, usdc_asset_id.value(), amount_to_creator
                ),
            )
        ),
        App.localPut(_sender, SUBSCRIPTION_STATUS, PREMIUM_SUBSCRIPTION),
        App.localPut(_sender, SUBSCRIPTION_PAYMENT_TYPE, _payment_type),
        App.localPut(_sender, SUBSCRIPTION_AMOUNT_PAID, _amount_to_receive),
        App.localPut(
            _sender, SUBSCRIPTION_DURATION, Minus(_new_expires_date, timestamp)
        ),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, _new_expires_date),
    )


@Subroutine(TealType.none)
def renew_creator():
    _sender = Txn.sender()
    _admin = Gtxn[2].sender()
    _payment_type = Btoi(Gtxn[2].application_args[1])
    _amount_to_receive = Btoi(Gtxn[2].application_args[2])
    _new_expires_date = Btoi(Gtxn[2].application_args[3])
    _creator_pool_address = Gtxn[2].accounts[1]

    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)
    app_address = Global.current_application_address()
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_status = App.localGet(_sender, SUBSCRIPTION_STATUS)

    timestamp = Global.latest_timestamp()
    amount_to_admin_fee = WideRatio([_amount_to_receive, Int(30)], [Int(100)])
    amount_to_creator = WideRatio([_amount_to_receive, Int(70)], [Int(100)])

    return Seq(
        usdc_asset_id,
        admin_address,
        _check_admin_role(_admin),
        Assert(Gt(_new_expires_date, timestamp)),
        Assert(Eq(subscription_status, PREMIUM_SUBSCRIPTION)),
        Assert(Or(Eq(_payment_type, ALGO), Eq(_payment_type, USDC))),
        If(Eq(_payment_type, ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                Assert(Eq(Gtxn[0].amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].receiver(), app_address)),
                Assert(Eq(Gtxn[0].sender(), _sender)),
                inner_payment_transaction(admin_address.value(), amount_to_admin_fee),
                inner_payment_transaction(_creator_pool_address, amount_to_creator),
            )
        ),
        If(Eq(_payment_type, USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset_id.value())),
                Assert(Eq(Gtxn[0].asset_amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].asset_receiver(), app_address)),
                Assert(Eq(Gtxn[0].asset_sender(), _sender)),
                inner_asset_transaction(
                    admin_address.value(), usdc_asset_id.value(), amount_to_admin_fee
                ),
                inner_asset_transaction(
                    _creator_pool_address, usdc_asset_id.value(), amount_to_creator
                ),
            )
        ),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, _new_expires_date),
    )


@Subroutine(TealType.none)
def subscribe_with_referral():
    _sender = Txn.sender()
    _admin = Gtxn[2].sender()
    _payment_type = Btoi(Gtxn[2].application_args[1])
    _amount_to_receive = Btoi(Gtxn[2].application_args[2])
    _new_expires_date = Btoi(Gtxn[2].application_args[3])
    _creator_pool_address = Gtxn[2].accounts[1]
    _referral_creator_address = Gtxn[2].accounts[2]

    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)
    app_address = Global.current_application_address()
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_status = App.localGet(_sender, SUBSCRIPTION_STATUS)

    timestamp = Global.latest_timestamp()
    expires_date = App.localGet(_sender, SUBSCRIPTION_EXPIRES_DATE)
    amount_to_admin_fee = WideRatio([_amount_to_receive, Int(50)], [Int(100)])
    creator_pool_fee = WideRatio([_amount_to_receive, Int(10)], [Int(100)])
    referral_creator_fee = WideRatio([_amount_to_receive, Int(40)], [Int(100)])

    return Seq(
        usdc_asset_id,
        admin_address,
        _check_admin_role(_admin),
        Assert(Eq(subscription_status, BASIC_SUBSCRIPTION)),
        Assert(Ge(timestamp, expires_date)),
        Assert(Gt(_new_expires_date, Global.latest_timestamp())),
        Assert(Or(Eq(_payment_type, ALGO), Eq(_payment_type, USDC))),
        If(Eq(_payment_type, ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                Assert(Eq(Gtxn[0].amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].receiver(), app_address)),
                Assert(Eq(Gtxn[0].sender(), _sender)),
                inner_payment_transaction(admin_address.value(), amount_to_admin_fee),
                inner_payment_transaction(
                    _referral_creator_address, referral_creator_fee
                ),
                increase_algo_pool_creator(_creator_pool_address, creator_pool_fee),
            )
        ),
        If(Eq(_payment_type, USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset_id.value())),
                Assert(Eq(Gtxn[0].asset_amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].asset_receiver(), app_address)),
                Assert(Eq(Gtxn[0].asset_sender(), _sender)),
                inner_asset_transaction(
                    admin_address.value(), usdc_asset_id.value(), amount_to_admin_fee
                ),
                inner_asset_transaction(
                    _referral_creator_address,
                    usdc_asset_id.value(),
                    referral_creator_fee,
                ),
                increase_asset_pool_creator(
                    _creator_pool_address, usdc_asset_id.value(), creator_pool_fee
                ),
            )
        ),
        App.localPut(_sender, SUBSCRIPTION_STATUS, PREMIUM_SUBSCRIPTION),
        App.localPut(_sender, SUBSCRIPTION_PAYMENT_TYPE, _payment_type),
        App.localPut(_sender, SUBSCRIPTION_AMOUNT_PAID, _amount_to_receive),
        App.localPut(
            _sender, SUBSCRIPTION_DURATION, Minus(_new_expires_date, timestamp)
        ),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, _new_expires_date),
    )


@Subroutine(TealType.none)
def renew_with_referral():
    _sender = Txn.sender()
    _admin = Gtxn[2].sender()
    _payment_type = Btoi(Gtxn[2].application_args[1])
    _amount_to_receive = Btoi(Gtxn[2].application_args[2])
    _new_expires_date = Btoi(Gtxn[2].application_args[3])
    _creator_pool_address = Gtxn[2].accounts[1]
    _referral_creator_address = Gtxn[2].accounts[2]

    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)
    app_address = Global.current_application_address()
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_status = App.localGet(_sender, SUBSCRIPTION_STATUS)

    timestamp = Global.latest_timestamp()
    amount_to_admin_fee = WideRatio([_amount_to_receive, Int(50)], [Int(100)])
    creator_pool_fee = WideRatio([_amount_to_receive, Int(10)], [Int(100)])
    referral_creator_fee = WideRatio([_amount_to_receive, Int(40)], [Int(100)])

    return Seq(
        usdc_asset_id,
        admin_address,
        _check_admin_role(_admin),
        Assert(Gt(_new_expires_date, timestamp)),
        Assert(Eq(subscription_status, PREMIUM_SUBSCRIPTION)),
        Assert(Or(Eq(_payment_type, ALGO), Eq(_payment_type, USDC))),
        If(Eq(_payment_type, ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                Assert(Eq(Gtxn[0].amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].receiver(), app_address)),
                Assert(Eq(Gtxn[0].sender(), _sender)),
                inner_payment_transaction(admin_address.value(), amount_to_admin_fee),
                inner_payment_transaction(
                    _referral_creator_address, referral_creator_fee
                ),
                increase_algo_pool_creator(_creator_pool_address, creator_pool_fee),
            )
        ),
        If(Eq(_payment_type, USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset_id.value())),
                Assert(Eq(Gtxn[0].asset_amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].asset_receiver(), app_address)),
                Assert(Eq(Gtxn[0].asset_sender(), _sender)),
                inner_asset_transaction(
                    admin_address.value(), usdc_asset_id.value(), amount_to_admin_fee
                ),
                inner_asset_transaction(
                    _referral_creator_address,
                    usdc_asset_id.value(),
                    referral_creator_fee,
                ),
                increase_asset_pool_creator(
                    _creator_pool_address, usdc_asset_id.value(), creator_pool_fee
                ),
            )
        ),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, _new_expires_date),
    )


@Subroutine(TealType.none)
def subscribe_platform():
    _sender = Txn.sender()
    _admin = Gtxn[2].sender()
    _payment_type = Btoi(Gtxn[2].application_args[1])
    _amount_to_receive = Btoi(Gtxn[2].application_args[2])
    _new_expires_date = Btoi(Gtxn[2].application_args[3])
    _creator_pool_address = Gtxn[2].accounts[1]

    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)
    app_address = Global.current_application_address()
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_status = App.localGet(_sender, SUBSCRIPTION_STATUS)

    timestamp = Global.latest_timestamp()
    expires_date = App.localGet(_sender, SUBSCRIPTION_EXPIRES_DATE)
    amount_to_admin_fee = WideRatio([_amount_to_receive, Int(50)], [Int(100)])
    creator_pool_fee = WideRatio([_amount_to_receive, Int(50)], [Int(100)])

    return Seq(
        usdc_asset_id,
        admin_address,
        _check_admin_role(_admin),
        Assert(Eq(subscription_status, BASIC_SUBSCRIPTION)),
        Assert(Ge(timestamp, expires_date)),
        Assert(Gt(_new_expires_date, Global.latest_timestamp())),
        Assert(Or(Eq(_payment_type, ALGO), Eq(_payment_type, USDC))),
        If(Eq(_payment_type, ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                Assert(Eq(Gtxn[0].amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].receiver(), app_address)),
                Assert(Eq(Gtxn[0].sender(), _sender)),
                inner_payment_transaction(admin_address.value(), amount_to_admin_fee),
                increase_algo_pool_creator(_creator_pool_address, creator_pool_fee),
            )
        ),
        If(Eq(_payment_type, USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset_id.value())),
                Assert(Eq(Gtxn[0].asset_amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].asset_receiver(), app_address)),
                Assert(Eq(Gtxn[0].asset_sender(), _sender)),
                inner_asset_transaction(
                    admin_address.value(), usdc_asset_id.value(), amount_to_admin_fee
                ),
                increase_asset_pool_creator(
                    _creator_pool_address, usdc_asset_id.value(), creator_pool_fee
                ),
            )
        ),
        App.localPut(_sender, SUBSCRIPTION_STATUS, PREMIUM_SUBSCRIPTION),
        App.localPut(_sender, SUBSCRIPTION_PAYMENT_TYPE, _payment_type),
        App.localPut(_sender, SUBSCRIPTION_AMOUNT_PAID, _amount_to_receive),
        App.localPut(
            _sender, SUBSCRIPTION_DURATION, Minus(_new_expires_date, timestamp)
        ),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, _new_expires_date),
    )


@Subroutine(TealType.none)
def renew_platform():
    _sender = Txn.sender()
    _admin = Gtxn[2].sender()
    _payment_type = Btoi(Gtxn[2].application_args[1])
    _amount_to_receive = Btoi(Gtxn[2].application_args[2])
    _new_expires_date = Btoi(Gtxn[2].application_args[3])
    _creator_pool_address = Gtxn[2].accounts[1]

    admin_id = App.globalGet(ADMIN_ID)
    admin_address = AppParam.address(admin_id)
    app_address = Global.current_application_address()
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)

    subscription_status = App.localGet(_sender, SUBSCRIPTION_STATUS)

    timestamp = Global.latest_timestamp()
    amount_to_admin_fee = WideRatio([_amount_to_receive, Int(50)], [Int(100)])
    creator_pool_fee = WideRatio([_amount_to_receive, Int(50)], [Int(100)])

    return Seq(
        usdc_asset_id,
        admin_address,
        _check_admin_role(_admin),
        Assert(Gt(_new_expires_date, timestamp)),
        Assert(Eq(subscription_status, PREMIUM_SUBSCRIPTION)),
        Assert(Or(Eq(_payment_type, ALGO), Eq(_payment_type, USDC))),
        If(Eq(_payment_type, ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                Assert(Eq(Gtxn[0].amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].receiver(), app_address)),
                Assert(Eq(Gtxn[0].sender(), _sender)),
                inner_payment_transaction(admin_address.value(), amount_to_admin_fee),
                increase_algo_pool_creator(_creator_pool_address, creator_pool_fee),
            )
        ),
        If(Eq(_payment_type, USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset_id.value())),
                Assert(Eq(Gtxn[0].asset_amount(), _amount_to_receive)),
                Assert(Eq(Gtxn[0].asset_receiver(), app_address)),
                Assert(Eq(Gtxn[0].asset_sender(), _sender)),
                inner_asset_transaction(
                    admin_address.value(), usdc_asset_id.value(), amount_to_admin_fee
                ),
                increase_asset_pool_creator(
                    _creator_pool_address, usdc_asset_id.value(), creator_pool_fee
                ),
            )
        ),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, _new_expires_date),
    )


@Subroutine(TealType.uint64)
def subscribe():
    _type_of_subscription = Btoi(Gtxn[2].application_args[4])

    return Seq(
        Assert(
            Or(
                Eq(_type_of_subscription, SUBSCRIBE_CREATOR),
                Eq(_type_of_subscription, SUBSCRIBE_REFERRAL),
                Eq(_type_of_subscription, SUBSCRIBE_PLATFORM),
            )
        ),
        If(Eq(_type_of_subscription, SUBSCRIBE_CREATOR)).Then(subscribe_creator()),
        If(Eq(_type_of_subscription, SUBSCRIBE_REFERRAL)).Then(
            subscribe_with_referral()
        ),
        If(Eq(_type_of_subscription, SUBSCRIBE_PLATFORM)).Then(subscribe_platform()),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def renew():
    _type_of_renew = Btoi(Gtxn[2].application_args[4])

    return Seq(
        Assert(
            Or(
                Eq(_type_of_renew, SUBSCRIBE_CREATOR),
                Eq(_type_of_renew, SUBSCRIBE_REFERRAL),
                Eq(_type_of_renew, SUBSCRIBE_PLATFORM),
            )
        ),
        If(Eq(_type_of_renew, SUBSCRIBE_CREATOR)).Then(renew_creator()),
        If(Eq(_type_of_renew, SUBSCRIBE_REFERRAL)).Then(renew_with_referral()),
        If(Eq(_type_of_renew, SUBSCRIBE_PLATFORM)).Then(renew_platform()),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def update_app():

    return Seq(_check_owner_role(), Return(Int(1)))


def subscription_app_approval():
    handle_noop = Cond(
        [utility_checker(), Return(Int(1))],
        [
            change_admin_id_checker(),
            Return(change_admin_id()),
        ],
        # * GROUP SIZE > 1
        [
            asset_optin_checker(),
            Return(usdc_asset_optin()),
        ],
        [
            renew_checker(),
            Return(renew()),
        ],
        [
            subscribe_checker(),
            Return(subscribe()),
        ],
    )

    program = Cond(
        [Txn.application_id() == Int(0), Return(deploy_contract())],
        [Txn.on_completion() == OnComplete.OptIn, Return(optin())],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(update_app())],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
    )
    return compileTeal(program, Mode.Application, version=6)


def subscription_app_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
