from pyteal import *
from contracts.checkers import (
    change_admin_id_checker,
    close_auction_checker,
    create_auction_checker,
    on_bid_auction_checker,
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
    START_AUCTION,
    END_AUCTION,
    MIN_BID_INCREMENT,
    CURRENT_BID,
    BIDDER_WINNER,
    PLATFORM_FEE,
    START_PRICE,
    MODULE_NAME,
    AUCTION_MODULE,
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
        App.globalPut(MODULE_NAME, AUCTION_MODULE),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def create_auction():
    _start_time = Btoi(Txn.application_args[1])
    _end_time = Btoi(Txn.application_args[2])
    _min_bid_increment = Btoi(Txn.application_args[3])
    _payment_option = Btoi(Txn.application_args[4])
    _start_price = Btoi(Txn.application_args[5])
    _nft_app_id = Txn.applications[1]
    _nft_id = Txn.assets[0]
    _sender = Txn.sender()

    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    nft_app_address = AppParam.address(_nft_app_id)
    nft_owner = App.globalGetEx(_nft_app_id, NFT_OWNER)

    return Seq(
        nft_id,
        nft_owner,
        nft_app_address,
        Assert(Gt(_start_time, Global.latest_timestamp())),
        Assert(Gt(_end_time, _start_time)),
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
        Assert(Ge(_start_price, Int(0))),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, START_AUCTION, Itob(_start_time), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, END_AUCTION, Itob(_end_time), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id,
            AUCTION_MODULE,
            MIN_BID_INCREMENT,
            Itob(_min_bid_increment),
            Itob(Int(1)),
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, CURRENT_BID, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id,
            AUCTION_MODULE,
            PAYMENT_OPTION,
            Itob(_payment_option),
            Itob(Int(1)),
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, START_PRICE, Itob(_start_price), Itob(Int(1))
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def on_bid_auction():
    _bidder = Txn.sender()
    _nft_app_id = Txn.applications[1]

    current_bid = App.globalGetEx(_nft_app_id, CURRENT_BID)
    min_bid_increment = App.globalGetEx(_nft_app_id, MIN_BID_INCREMENT)
    bidder_winner = App.globalGetEx(_nft_app_id, BIDDER_WINNER)
    payment_option = App.globalGetEx(_nft_app_id, PAYMENT_OPTION)
    usdc_asset = App.globalGetEx(_nft_app_id, USDC_ASSET_ID)
    start_price = App.globalGetEx(_nft_app_id, START_PRICE)
    start_auction = App.globalGetEx(_nft_app_id, START_AUCTION)
    end_auction = App.globalGetEx(_nft_app_id, END_AUCTION)

    nft_app_address = AppParam.address(_nft_app_id)

    bid_amount = ScratchVar(TealType.uint64)
    minimum_bid_amount = ScratchVar(TealType.uint64)

    return Seq(
        current_bid,
        min_bid_increment,
        bidder_winner,
        payment_option,
        usdc_asset,
        start_price,
        nft_app_address,
        start_auction,
        end_auction,
        minimum_bid_amount.store(Add(current_bid.value(), min_bid_increment.value())),
        bid_amount.store(Int(0)),
        Assert(
            Or(
                Eq(Gtxn[0].receiver(), nft_app_address.value()),
                Eq(Gtxn[0].asset_receiver(), nft_app_address.value()),
            ),
        ),
        If(Eq(payment_option.value(), ALGO)).Then(
            Seq(
                Assert(Eq(Gtxn[0].type_enum(), TxnType.Payment)),
                bid_amount.store(Gtxn[0].amount()),
            )
        ),
        If(Eq(payment_option.value(), USDC)).Then(
            Seq(
                Assert(Eq(Gtxn[0].xfer_asset(), usdc_asset.value())),
                bid_amount.store(Gtxn[0].asset_amount()),
            )
        ),
        Assert(Ge(Global.latest_timestamp(), start_auction.value())),
        Assert(Lt(Global.latest_timestamp(), end_auction.value())),
        Assert(Ge(bid_amount.load(), minimum_bid_amount.load())),
        Assert(Neq(bid_amount.load(), Int(0))),
        Assert(Ge(bid_amount.load(), start_price.value())),
        If(Gt(current_bid.value(), Int(0))).Then(
            Seq(
                If(Eq(payment_option.value(), ALGO)).Then(
                    pay_algo_txn(
                        _nft_app_id,
                        bidder_winner.value(),
                        current_bid.value(),
                        AUCTION_MODULE,
                    )
                ),
                If(Eq(payment_option.value(), USDC)).Then(
                    pay_asset_txn(
                        _nft_app_id,
                        bidder_winner.value(),
                        usdc_asset.value(),
                        current_bid.value(),
                        AUCTION_MODULE,
                    )
                ),
            )
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, BIDDER_WINNER, _bidder, Itob(Int(0))
        ),
        set_global_txn(
            _nft_app_id,
            AUCTION_MODULE,
            CURRENT_BID,
            Itob(bid_amount.load()),
            Itob(Int(1)),
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.none)
def close_auction_before():
    _nft_id = Txn.assets[0]
    _nft_app_id = Txn.applications[1]
    _sender = Txn.sender()

    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    nft_owner = App.globalGetEx(_nft_app_id, NFT_OWNER)

    return Seq(
        nft_id,
        nft_owner,
        Assert(Eq(_nft_id, nft_id.value())),
        Assert(Eq(_sender, nft_owner.value())),
        pay_asset_txn(_nft_app_id, _sender, _nft_id, Int(1), AUCTION_MODULE),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, START_AUCTION, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, END_AUCTION, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, MIN_BID_INCREMENT, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, CURRENT_BID, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, BIDDER_WINNER, Bytes(""), Itob(Int(0))
        ),
        Log(Bytes("BEFORE")),
    )


@Subroutine(TealType.none)
def close_auction_after():
    _sender = Txn.sender()
    _nft_id = Txn.assets[0]
    _nft_app_id = Txn.applications[1]

    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    nft_owner = App.globalGetEx(_nft_app_id, NFT_OWNER)

    return Seq(
        nft_id,
        nft_owner,
        Assert(Eq(nft_owner.value(), _sender)),
        Assert(Eq(_nft_id, nft_id.value())),
        pay_asset_txn(_nft_app_id, _sender, _nft_id, Int(1), AUCTION_MODULE),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, START_AUCTION, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, END_AUCTION, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, MIN_BID_INCREMENT, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, CURRENT_BID, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, BIDDER_WINNER, Bytes(""), Itob(Int(0))
        ),
        Log(Bytes("AFTER")),
    )


@Subroutine(TealType.none)
def close_auction_winner():
    _nft_id = Txn.assets[0]
    _sender = Txn.sender()
    _nft_creator = Txn.accounts[1]
    _bidder_winner = Txn.accounts[2]
    _admin_address = Txn.accounts[3]
    _nft_app_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)
    nft_creator = App.globalGetEx(_nft_app_id, NFT_CREATOR)
    nft_id = App.globalGetEx(_nft_app_id, NFT_ID)
    royalty = App.globalGetEx(_nft_app_id, ROYALTY)
    current_bid = App.globalGetEx(_nft_app_id, CURRENT_BID)
    payment_option = App.globalGetEx(_nft_app_id, PAYMENT_OPTION)
    usdc_asset = App.globalGetEx(_nft_app_id, USDC_ASSET_ID)
    bidder_winner = App.globalGetEx(_nft_app_id, BIDDER_WINNER)
    platform_fee = App.globalGetEx(admin_id, PLATFORM_FEE)
    admin_address = AppParam.address(admin_id)

    fee_to_platform = ScratchVar(TealType.uint64)
    nft_creator_amount = ScratchVar(TealType.uint64)
    owner_amount = ScratchVar(TealType.uint64)

    return Seq(
        platform_fee,
        admin_address,
        nft_creator,
        nft_id,
        royalty,
        current_bid,
        payment_option,
        usdc_asset,
        bidder_winner,
        nft_creator_amount.store(
            WideRatio([current_bid.value(), royalty.value()], [Int(100)])
        ),
        Assert(Eq(_admin_address, admin_address.value())),
        Assert(Eq(_bidder_winner, bidder_winner.value())),
        fee_to_platform.store(
            WideRatio([platform_fee.value(), current_bid.value()], [Int(100)])
        ),
        owner_amount.store(
            Minus(
                current_bid.value(),
                Add(nft_creator_amount.load(), fee_to_platform.load()),
            )
        ),
        Assert(Eq(_nft_id, nft_id.value())),
        Assert(Eq(_nft_creator, nft_creator.value())),
        If(Eq(payment_option.value(), ALGO)).Then(
            Seq(
                pay_algo_txn(
                    _nft_app_id, _admin_address, fee_to_platform.load(), AUCTION_MODULE
                ),
                pay_algo_txn(
                    _nft_app_id, _nft_creator, nft_creator_amount.load(), AUCTION_MODULE
                ),
                pay_algo_txn(_nft_app_id, _sender, owner_amount.load(), AUCTION_MODULE),
                pay_asset_txn(
                    _nft_app_id, _bidder_winner, nft_id.value(), Int(1), AUCTION_MODULE
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
                    AUCTION_MODULE,
                ),
                pay_asset_txn(
                    _nft_app_id,
                    _nft_creator,
                    usdc_asset.value(),
                    nft_creator_amount.load(),
                    AUCTION_MODULE,
                ),
                pay_asset_txn(
                    _nft_app_id,
                    _sender,
                    usdc_asset.value(),
                    owner_amount.load(),
                    AUCTION_MODULE,
                ),
                pay_asset_txn(
                    _nft_app_id,
                    _bidder_winner,
                    nft_id.value(),
                    Int(1),
                    AUCTION_MODULE,
                ),
            )
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, START_AUCTION, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, END_AUCTION, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, MIN_BID_INCREMENT, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, CURRENT_BID, Itob(Int(0)), Itob(Int(1))
        ),
        set_global_txn(
            _nft_app_id, AUCTION_MODULE, NFT_OWNER, _bidder_winner, Itob(Int(0))
        ),
        del_global_txn(_nft_app_id, AUCTION_MODULE, PAYMENT_OPTION),
        Log(Bytes("WINNER")),
        Log(_bidder_winner),
    )


@Subroutine(TealType.uint64)
def close_auction():
    _nft_app_id = Txn.applications[1]

    start_auction = App.globalGetEx(_nft_app_id, START_AUCTION)
    end_auction = App.globalGetEx(_nft_app_id, END_AUCTION)
    current_bid = App.globalGetEx(_nft_app_id, CURRENT_BID)

    return Seq(
        start_auction,
        end_auction,
        current_bid,
        Log(Itob(Global.latest_timestamp())),
        Log(Itob(start_auction.value())),
        Log(Itob(end_auction.value())),
        If(Lt(Global.latest_timestamp(), start_auction.value())).Then(
            Seq(close_auction_before(), Approve())
        ),
        If(Gt(Global.latest_timestamp(), end_auction.value())).Then(
            Seq(
                If(Eq(current_bid.value(), Int(0)))
                .Then(Seq(close_auction_after(), Approve()))
                .Else(Seq(close_auction_winner(), Approve()))
            )
        ),
        Return(Int(0)),
    )


@Subroutine(TealType.uint64)
def change_admin_id():
    _sender = Txn.sender()
    _new_admin_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)
    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        App.globalPut(ADMIN_ID, _new_admin_id),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def update_app():

    return Seq(_check_owner_role(), Return(Int(1)))


def auction_approval():
    handle_noop = Cond(
        # * Group transaction === 1
        [
            close_auction_checker(),
            Return(close_auction()),
        ],
        [
            change_admin_id_checker(),
            Return(change_admin_id()),
        ],
        # * Group transaction > 1
        [
            create_auction_checker(),
            Return(create_auction()),
        ],
        [
            on_bid_auction_checker(),
            Return(on_bid_auction()),
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


def auction_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
