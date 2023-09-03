from pyteal import *
from contracts.checkers import (
    change_admin_id_checker,
    purchase_nft_checker,
    revert_nft_checker,
    start_sell_checker,
)
from contracts.constants import (
    ADMIN_ID,
    ADMIN_ROLE,
    ALGO,
    NEW_ADMIN_ID,
    NFT_ID,
    NFT_OWNER,
    NFT_CREATOR,
    USDC,
    PAYMENT_OPTION,
    ROLE,
    ROYALTY,
    USDC_ASSET_ID,
    PLATFORM_FEE,
    MODULE_NAME,
    LIST_MODULE,
    NFT_PRICE,
)
from contracts.utility import (
    set_global_txn,
    pay_asset_txn,
    pay_algo_txn,
    del_global_txn,
    _check_owner_role,
)


@Subroutine(TealType.uint64)
def deploy_contract():
    _admin_id = Txn.applications[1]

    return Seq(
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(MODULE_NAME, LIST_MODULE),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def start_sell():
    _nft_price = Btoi(Txn.application_args[1])
    _payment_option = Btoi(Txn.application_args[2])
    _nft_id = Txn.assets[0]
    _sender = Txn.sender()
    _nft_app_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)
    platform_fee = App.globalGetEx(admin_id, PLATFORM_FEE)
    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    nft_owner = App.globalGetEx(_nft_app_id, NFT_OWNER)

    nft_app_address = AppParam.address(_nft_app_id)

    return Seq(
        platform_fee,
        nft_id,
        nft_owner,
        nft_app_address,
        Assert(Eq(_nft_id, nft_id.value())),
        Assert(Eq(_sender, nft_owner.value())),
        Assert(Eq(Gtxn[0].asset_receiver(), nft_app_address.value())),
        Assert(Eq(Gtxn[0].xfer_asset(), nft_id.value())),
        Assert(
            Or(
                Eq(_payment_option, ALGO),
                Eq(_payment_option, USDC),
            )
        ),
        set_global_txn(
            _nft_app_id,
            LIST_MODULE,
            NFT_PRICE,
            Itob(_nft_price),
            Itob(Int(1)),
        ),
        set_global_txn(
            _nft_app_id,
            LIST_MODULE,
            PLATFORM_FEE,
            Itob(platform_fee.value()),
            Itob(Int(1)),
        ),
        set_global_txn(
            _nft_app_id,
            LIST_MODULE,
            PAYMENT_OPTION,
            Itob(_payment_option),
            Itob(Int(1)),
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def revert_nft():
    _sender = Txn.sender()
    _nft_id = Txn.assets[0]
    _nft_app_id = Txn.applications[1]

    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    nft_owner = App.globalGetEx(_nft_app_id, NFT_OWNER)

    return Seq(
        nft_id,
        nft_owner,
        Assert(Eq(_sender, nft_owner.value())),
        Assert(Eq(_nft_id, nft_id.value())),
        pay_asset_txn(
            _nft_app_id, nft_owner.value(), nft_id.value(), Int(1), LIST_MODULE
        ),
        set_global_txn(
            _nft_app_id,
            LIST_MODULE,
            NFT_PRICE,
            Itob(Int(0)),
            Itob(Int(1)),
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def purchase_nft():
    _sender = Txn.sender()
    _nft_owner = Txn.accounts[1]
    _nft_creator = Txn.accounts[2]
    _admin_address = Txn.accounts[3]
    _nft_id = Txn.assets[0]
    _nft_app_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)

    platform_fee = App.globalGetEx(admin_id, PLATFORM_FEE)
    nft_owner = App.globalGetEx(_nft_app_id, NFT_OWNER)
    nft_price = App.globalGetEx(_nft_app_id, NFT_PRICE)
    royalty = App.globalGetEx(_nft_app_id, ROYALTY)
    nft_creator = App.globalGetEx(_nft_app_id, NFT_CREATOR)
    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    payment_option = App.globalGetEx(_nft_app_id, PAYMENT_OPTION)
    usdc_asset = App.globalGetEx(_nft_app_id, USDC_ASSET_ID)

    admin_address = AppParam.address(admin_id)
    nft_app_address = AppParam.address(_nft_app_id)

    royalty_fee = ScratchVar(TealType.uint64)
    fee_to_platform = ScratchVar(TealType.uint64)
    rest_amount = ScratchVar(TealType.uint64)
    payment_amount = ScratchVar(TealType.uint64)

    return Seq(
        admin_address,
        nft_app_address,
        platform_fee,
        nft_owner,
        nft_price,
        royalty,
        nft_creator,
        nft_id,
        payment_option,
        usdc_asset,
        royalty_fee.store(WideRatio([royalty.value(), nft_price.value()], [Int(100)])),
        payment_amount.store(Int(0)),
        fee_to_platform.store(
            WideRatio([platform_fee.value(), nft_price.value()], [Int(100)])
        ),
        rest_amount.store(
            Minus(nft_price.value(), Add(fee_to_platform.load(), royalty_fee.load()))
        ),
        Assert(Eq(_nft_creator, nft_creator.value())),
        Assert(Eq(_nft_owner, nft_owner.value())),
        Assert(Eq(_admin_address, admin_address.value())),
        Assert(
            Or(
                Eq(Gtxn[0].receiver(), nft_app_address.value()),
                Eq(Gtxn[0].asset_receiver(), nft_app_address.value()),
            )
        ),
        If(Eq(payment_option.value(), ALGO)).Then(
            payment_amount.store(Gtxn[0].amount())
        ),
        If(Eq(payment_option.value(), USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset.value())),
                payment_amount.store(Gtxn[0].asset_amount()),
            )
        ),
        Assert(Eq(payment_amount.load(), nft_price.value())),
        Assert(Eq(_nft_id, nft_id.value())),
        If(Eq(payment_option.value(), ALGO)).Then(
            Seq(
                pay_algo_txn(
                    _nft_app_id, _admin_address, fee_to_platform.load(), LIST_MODULE
                ),
                pay_algo_txn(
                    _nft_app_id, _nft_creator, royalty_fee.load(), LIST_MODULE
                ),
                pay_algo_txn(_nft_app_id, _nft_owner, rest_amount.load(), LIST_MODULE),
                pay_asset_txn(
                    _nft_app_id, _sender, nft_id.value(), Int(1), LIST_MODULE
                ),
            )
        ),
        If(Eq(payment_option.value(), USDC)).Then(
            Seq(
                pay_asset_txn(
                    _nft_app_id,
                    _admin_address,
                    usdc_asset.value(),
                    fee_to_platform.load(),
                    LIST_MODULE,
                ),
                pay_asset_txn(
                    _nft_app_id,
                    _nft_creator,
                    usdc_asset.value(),
                    royalty_fee.load(),
                    LIST_MODULE,
                ),
                pay_asset_txn(
                    _nft_app_id,
                    _nft_owner,
                    usdc_asset.value(),
                    rest_amount.load(),
                    LIST_MODULE,
                ),
                pay_asset_txn(
                    _nft_app_id, _sender, nft_id.value(), Int(1), LIST_MODULE
                ),
            )
        ),
        set_global_txn(
            _nft_app_id,
            LIST_MODULE,
            NFT_PRICE,
            Itob(Int(0)),
            Itob(Int(1)),
        ),
        set_global_txn(
            _nft_app_id,
            LIST_MODULE,
            NFT_OWNER,
            _sender,
            Itob(Int(0)),
        ),
        del_global_txn(_nft_app_id, LIST_MODULE, PAYMENT_OPTION),
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


def list_approval():
    handle_noop = Cond(
        # * Group transaction === 1
        [
            revert_nft_checker(),
            Return(revert_nft()),
        ],
        [
            change_admin_id_checker(),
            Return(change_admin_id()),
        ],
        # * Group transaction >= 1
        [
            start_sell_checker(),
            Return(start_sell()),
        ],
        [
            purchase_nft_checker(),
            Return(purchase_nft()),
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
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(update_app())],
    )

    return compileTeal(program, Mode.Application, version=6)


def list_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
