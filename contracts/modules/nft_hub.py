from pyteal import *
from contracts.constants import *
from contracts.utility import (
    inner_contract_payment_transaction,
)


@Subroutine(TealType.uint64)
def deploy_hub():
    _creator_app = Global.caller_app_id()
    _royalty = Btoi(Txn.application_args[0])
    _admin_id = Txn.applications[1]
    _nft_owner = Txn.accounts[1]
    # _nft_id = Txn.assets[0]
    _usdc_asset = Txn.assets[1]

    admin_address = AppParam.address(_admin_id)
    # nft_clawback = AssetParam.clawback(_nft_id)
    # nft_freeze = AssetParam.freeze(_nft_id)
    # nft_default_freeze = AssetParam.defaultFrozen(_nft_id)
    # nft_decimals = AssetParam.decimals(_nft_id)
    # nft_total_supply = AssetParam.total(_nft_id)
    # nft_manager = AssetParam.manager(_nft_id)
    # nft_creator = AssetParam.creator(_nft_id)
    zero_address = Global.zero_address()

    creator_address = App.globalGetEx(_creator_app, CREATOR_ADDRESS)

    return Seq(
        admin_address,
        # nft_clawback,
        # nft_freeze,
        # nft_default_freeze,
        # nft_decimals,
        # nft_manager,
        # nft_total_supply,
        # nft_creator,
        creator_address,
        # Assert(Eq(nft_default_freeze.value(), Int(0))),
        # Assert(Eq(nft_clawback.value(), zero_address)),
        # Assert(Eq(nft_freeze.value(), zero_address)),
        # Assert(Eq(nft_manager.value(), admin_address.value())),
        # Assert(Eq(nft_decimals.value(), Int(0))),
        # Assert(Eq(nft_total_supply.value(), Int(1))),
        # App.globalPut(NFT_ID, _nft_id),
        # App.globalPut(NFT_CREATOR, nft_creator.value()),
        Assert(Ge(_royalty, Int(1))),
        Assert(Le(_royalty, Int(50))),
        Assert(Eq(creator_address.value(), _nft_owner)),
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(NFT_OWNER, _nft_owner),
        App.globalPut(ROYALTY, _royalty),
        App.globalPut(USDC_ASSET_ID, _usdc_asset),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def create_space(space_approval, space_clear):
    _royalty = Btoi(Txn.application_args[1])
    _nft_owner = Txn.sender()
    _nft_id = Txn.assets[0]

    admin_id = App.globalGet(ADMIN_ID)
    creator_address = App.globalGet(CREATOR_ADDRESS)
    usdc_asset = App.globalGetEx(admin_id, USDC_ASSET_ID)
    nft_owner = AssetHolding.balance(_nft_owner, _nft_id)

    nft_app_id = ScratchVar(TealType.uint64)

    return Seq(
        usdc_asset,
        nft_owner,
        # * Check if the nft owner is the caller
        Assert(Eq(_nft_owner, nft_owner.value())),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.approval_program: space_approval,
                TxnField.clear_state_program: space_clear,
                TxnField.application_args: [Itob(_royalty)],
                TxnField.applications: [admin_id, Global.current_application_id()],
                TxnField.accounts: [_nft_owner, creator_address],
                TxnField.assets: [_nft_id, usdc_asset.value()],
                TxnField.fee: Int(0),
                TxnField.local_num_uints: Int(0),
                TxnField.local_num_byte_slices: Int(0),
                TxnField.global_num_uints: Int(13),
                TxnField.global_num_byte_slices: Int(9),
                TxnField.extra_program_pages: Int(2),
            }
        ),
        InnerTxnBuilder.Submit(),
        nft_app_id.store(InnerTxn.created_application_id()),
        inner_contract_payment_transaction(nft_app_id.load(), Int(100_000)),
        Return(Int(1)),
    )


def nft_hub_approval():
    handle_noop = Cond()

    program = Cond(
        [
            And(
                Eq(Txn.application_id(), Int(0)),
                Eq(Global.group_size(), Int(1)),
                Eq(Txn.rekey_to(), Global.zero_address()),
            ),
            Return(deploy_hub()),
        ],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
    )

    return compileTeal(program, Mode.Application, version=6)


def nft_hub_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
