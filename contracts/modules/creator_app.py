from pyteal import *
from contracts.checkers import (
    change_admin_id_checker,
    create_asset_app_checker,
    asset_optin_checker,
    utility_checker,
)
from contracts.constants import *
from contracts.utility import (
    inner_contract_payment_transaction,
    _check_owner_role,
)


@Subroutine(TealType.uint64)
def deploy_contract():
    _admin_id = Txn.applications[1]
    _creator_address = Txn.accounts[1]

    return Seq(
        App.globalPut(ADMIN_ID, _admin_id),
        App.globalPut(MODULE_NAME, CREATOR_APP),
        App.globalPut(CREATOR_ADDRESS, _creator_address),
        App.globalPut(SUBSCRIPTION, Int(0)),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def create_asset_app(asset_program_approval, nft_app_clear_program):
    _royalty = Btoi(Txn.application_args[1])
    _nft_owner = Txn.sender()
    _nft_id = Txn.assets[0]

    admin_id = App.globalGet(ADMIN_ID)
    creator_address = App.globalGet(CREATOR_ADDRESS)
    usdc_asset_id = App.globalGetEx(admin_id, USDC_ASSET_ID)
    nft_app_id = ScratchVar(TealType.uint64)

    return Seq(
        usdc_asset_id,
        Assert(Eq(_nft_owner, creator_address)),
        Assert(Ge(_royalty, Int(1))),
        Assert(Le(_royalty, Int(50))),
        Assert(Eq(usdc_asset_id.hasValue(), Int(1))),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.approval_program: asset_program_approval,
                TxnField.clear_state_program: nft_app_clear_program,
                TxnField.application_args: [Itob(_royalty)],
                TxnField.applications: [admin_id, Global.current_application_id()],
                TxnField.accounts: [_nft_owner],
                TxnField.assets: [_nft_id, usdc_asset_id.value()],
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
        Log(Itob(nft_app_id.load())),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def usdc_asset_optin():
    _sender = Txn.sender()
    _usdc_asset_id = Txn.assets[0]

    creator_address = App.globalGet(CREATOR_ADDRESS)

    return Seq(
        Assert(Eq(_sender, creator_address)),
        App.globalPut(USDC_ASSET_ID, _usdc_asset_id),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.asset_amount: Int(0),
                TxnField.xfer_asset: _usdc_asset_id,
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

    return Seq(
        App.localPut(_sender, SUBSCRIPTION_STATUS, BASIC_SUBSCRIPTION),
        App.localPut(_sender, SUBSCRIPTION_EXPIRES_DATE, Int(0)),
        App.localPut(_sender, CREATOR_ADDRESS, Global.creator_address()),
        Return(Int(1)),
    )


@Subroutine(TealType.uint64)
def update_app():

    return Seq(_check_owner_role(), Return(Int(1)))


def creator_app_approval(nft_app_approval_program, nft_app_clear_program):
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
            create_asset_app_checker(),
            Return(
                create_asset_app(
                    Bytes("base64", nft_app_approval_program),
                    Bytes("base64", nft_app_clear_program),
                )
            ),
        ],
    )

    program = Cond(
        [Txn.application_id() == Int(0), Return(deploy_contract())],
        [Txn.on_completion() == OnComplete.OptIn, Return(optin())],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(1))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(update_app())],
    )
    return compileTeal(program, Mode.Application, version=6)


def creator_app_clear():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)

def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response["result"])
