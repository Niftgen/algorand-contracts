from pyteal import *
from contracts.checkers import (
    change_admin_id_checker,
    del_global_checker,
    opt_in_assets_checker,
    pay_algo_checker,
    pay_asset_checker,
    set_global_checker,
)
from contracts.constants import (
    ADMIN_ID,
    CREATOR_ADDRESS,
    NEW_ADMIN_ID,
    NFT_ID,
    NFT_OWNER,
    NFT_CREATOR,
    ROYALTY,
    USDC_ASSET_ID,
    CURRENT_BID,
    BIDDER_WINNER,
    ADMIN_ROLE,
    ROLE,
)
from contracts.utility import (
    send_asset_txn,
    inner_payment_transaction,
    _check_owner_role,
)


@Subroutine(TealType.uint64)
def deploy_contract():
    _royalty = Btoi(Txn.application_args[0])
    _admin_id = Txn.applications[1]
    _nft_owner = Txn.accounts[1]
    _nft_id = Txn.assets[0]
    _usdc_asset = Txn.assets[1]
    _sender = Global.caller_app_id()

    admin_address = AppParam.address(_admin_id)
    nft_clawback = AssetParam.clawback(_nft_id)
    nft_freeze = AssetParam.freeze(_nft_id)
    nft_default_freeze = AssetParam.defaultFrozen(_nft_id)
    nft_decimals = AssetParam.decimals(_nft_id)
    nft_total_supply = AssetParam.total(_nft_id)
    nft_manager = AssetParam.manager(_nft_id)
    zero_address = Global.zero_address()
    nft_creator = AssetParam.creator(_nft_id)

    creator_address = App.globalGetEx(_sender, CREATOR_ADDRESS)

    return Seq(
        admin_address,
        nft_clawback,
        nft_freeze,
        nft_default_freeze,
        nft_decimals,
        nft_manager,
        nft_total_supply,
        nft_creator,
        creator_address,
        Assert(Eq(creator_address.value(), _nft_owner)),
        Assert(Eq(nft_default_freeze.value(), Int(0))),
        Assert(Eq(nft_clawback.value(), zero_address)),
        Assert(Eq(nft_freeze.value(), zero_address)),
        Assert(Eq(nft_manager.value(), admin_address.value())),
        Assert(Eq(nft_decimals.value(), Int(0))),
        Assert(Eq(nft_total_supply.value(), Int(1))),
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(NFT_ID, _nft_id),
        App.globalPut(NFT_OWNER, _nft_owner),
        App.globalPut(NFT_CREATOR, nft_creator.value()),
        App.globalPut(ROYALTY, _royalty),
        App.globalPut(USDC_ASSET_ID, _usdc_asset),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def opt_in_assets():
    _nft_id = Txn.assets[0]
    _usdc_asset = Txn.assets[1]
    _admin_id = Txn.applications[1]

    app_address = Global.current_application_address()
    nft_id = App.globalGet(NFT_ID)
    admin_id = App.globalGet(ADMIN_ID)
    usdc_asset = App.globalGet(USDC_ASSET_ID)

    return Seq(
        Assert(Eq(nft_id, _nft_id)),
        Assert(Eq(_admin_id, admin_id)),
        Assert(Eq(_usdc_asset, usdc_asset)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: nft_id,
                TxnField.asset_receiver: app_address,
                TxnField.asset_amount: Int(0),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: app_address,
                TxnField.asset_amount: Int(0),
                TxnField.xfer_asset: _usdc_asset,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def delete_app():
    _sender = Txn.sender()

    admin_id = App.globalGet(ADMIN_ID)
    bid_amount = App.globalGet(CURRENT_BID)
    bidder_winner = App.globalGet(BIDDER_WINNER)

    sender_role = App.localGetEx(_sender, admin_id, ROLE)

    return Seq(
        sender_role,
        Assert(Eq(sender_role.value(), ADMIN_ROLE)),
        If(Gt(bid_amount, Int(0))).Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.amount: bid_amount,
                        TxnField.receiver: bidder_winner,
                        TxnField.fee: Int(0),
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def pay_algo():
    _sender_id = Global.caller_app_id()
    _module_name = Txn.application_args[1]
    _admin_id = Txn.applications[1]
    _beneficiary = Txn.accounts[1]
    _amount = Btoi(Txn.application_args[2])

    admin_id = App.globalGet(ADMIN_ID)
    module_id = App.globalGetEx(admin_id, _module_name)

    return Seq(
        module_id,
        Assert(Eq(_admin_id, admin_id)),
        Assert(Neq(_sender_id, Int(0))),
        Assert(Eq(_sender_id, module_id.value())),
        inner_payment_transaction(_beneficiary, _amount),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def pay_asset():
    _sender_id = Global.caller_app_id()
    _module_name = Txn.application_args[1]
    _admin_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)
    module_id = App.globalGetEx(admin_id, _module_name)

    return Seq(
        module_id,
        Assert(Eq(_admin_id, admin_id)),
        Assert(Neq(_sender_id, Int(0))),
        Assert(Eq(_sender_id, module_id.value())),
        send_asset_txn(),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def set_global():
    _sender_id = Global.caller_app_id()
    _module_name = Txn.application_args[1]
    _global_name = Txn.application_args[2]
    _global_value = Txn.application_args[3]
    _global_int = Btoi(Txn.application_args[4])
    _admin_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)
    module_id = App.globalGetEx(admin_id, _module_name)

    return Seq(
        module_id,
        Assert(Eq(_admin_id, admin_id)),
        Assert(Neq(_sender_id, Int(0))),
        Assert(Eq(_sender_id, module_id.value())),
        # * If the global_int is 0 the value is in bytes otherwise is a number
        If(Eq(_global_int, Int(0)))
        .Then(
            App.globalPut(_global_name, _global_value),
        )
        .Else(
            App.globalPut(_global_name, Btoi(_global_value)),
        ),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def remove_global():
    _sender_id = Global.caller_app_id()
    _module_name = Txn.application_args[1]
    _global_name = Txn.application_args[2]
    _admin_id = Txn.applications[1]

    admin_id = App.globalGet(ADMIN_ID)
    module_id = App.globalGetEx(admin_id, _module_name)

    return Seq(
        module_id,
        Assert(Eq(_admin_id, admin_id)),
        Assert(Neq(_sender_id, Int(0))),
        Assert(Eq(_sender_id, module_id.value())),
        App.globalDel(_global_name),
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


def nft_app_approval():
    handle_noop = Cond(
        # * Group transaction = 1
        [
            set_global_checker(),
            Return(set_global()),
        ],
        [
            pay_algo_checker(),
            Return(pay_algo()),
        ],
        [
            pay_asset_checker(),
            Return(pay_asset()),
        ],
        [
            del_global_checker(),
            Return(remove_global()),
        ],
        [
            change_admin_id_checker(),
            Return(change_admin_id()),
        ],
        # * Group transaction > 1
        [
            opt_in_assets_checker(),
            Return(opt_in_assets()),
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
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(delete_app())],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(update_app())],
    )

    return compileTeal(program, Mode.Application, version=6)


def nft_app_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
