from pyteal import *
from contracts.constants import (
    ADMIN_ID,
    PAY_ALGO,
    PAY_ASSET,
    SET_GLOBAL,
    DEL_GLOBAL,
    ROLE,
    ADMIN_ROLE,
    SET_LOCAL,
    CREATOR_POOL,
    INCREASE_ALGO_POOL,
    INCREASE_ASSET_POOL_REWARDS,
    OWNER,
)


@Subroutine(TealType.uint64)
def inner_nft_creation(name, unit_name, total, creator_address, metadata):
    """
    - returns the id of the generated asset or fails
    """

    return Seq(
        If(Eq(metadata, Bytes("")))
        .Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.AssetConfig,
                        TxnField.config_asset_name: name,
                        TxnField.config_asset_clawback: creator_address,
                        TxnField.config_asset_freeze: creator_address,
                        TxnField.config_asset_manager: creator_address,
                        TxnField.config_asset_unit_name: unit_name,
                        TxnField.config_asset_total: total,
                        TxnField.config_asset_decimals: Int(0),
                        TxnField.fee: Int(0),
                    }
                ),
                InnerTxnBuilder.Submit(),
                Return(InnerTxn.created_asset_id()),
            )
        )
        .Else(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.AssetConfig,
                        TxnField.config_asset_name: name,
                        TxnField.config_asset_clawback: creator_address,
                        TxnField.config_asset_freeze: creator_address,
                        TxnField.config_asset_manager: creator_address,
                        TxnField.config_asset_unit_name: unit_name,
                        TxnField.config_asset_total: total,
                        TxnField.config_asset_metadata_hash: metadata,
                        TxnField.config_asset_decimals: Int(0),
                        TxnField.fee: Int(0),
                    }
                ),
                InnerTxnBuilder.Submit(),
                Return(InnerTxn.created_asset_id()),
            )
        )
    )


@Subroutine(TealType.none)
def inner_payment_transaction(beneficiary, algo_amount):

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.sender: Global.current_application_address(),
                TxnField.amount: algo_amount,
                TxnField.receiver: beneficiary,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def inner_contract_payment_transaction(asset_app_id, algo_amount):
    asset_app_address = AppParam.address(asset_app_id)

    return Seq(
        asset_app_address,
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.sender: Global.current_application_address(),
                TxnField.amount: algo_amount,
                TxnField.receiver: asset_app_address.value(),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def add_module_txn():
    _module_id = Txn.applications[1]

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.application_id: _module_id,
                TxnField.application_args: Txn.application_args,
                TxnField.fee: Int(0),
                TxnField.accounts: Txn.accounts,
                TxnField.assets: Txn.assets,
                TxnField.applications: Txn.applications,
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def send_asset_txn():
    _asset_amount = Btoi(Txn.application_args[2])
    _asset_id = Txn.assets[0]
    _asset_receiver = Txn.accounts[1]

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: _asset_id,
                TxnField.asset_receiver: _asset_receiver,
                TxnField.asset_amount: _asset_amount,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def pay_algo_txn(app_id, beneficiary, amount, module_name):
    admin_id = App.globalGet(ADMIN_ID)

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: app_id,
                TxnField.application_args: [PAY_ALGO, module_name, Itob(amount)],
                TxnField.accounts: [beneficiary],
                TxnField.applications: [admin_id],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def pay_asset_txn(app_id, beneficiary, asset, amount, module_name):
    admin_id = App.globalGet(ADMIN_ID)

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: app_id,
                TxnField.application_args: [PAY_ASSET, module_name, Itob(amount)],
                TxnField.assets: [asset],
                TxnField.accounts: [beneficiary],
                TxnField.applications: [admin_id],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def set_global_txn(app_id, module_name, global_name, global_value, global_int):
    """
    app_id: uint
    module_name: bytes
    global_name: bytes
    global_value: bytes
    global_int: indicate if global_value is a number (1 True - 0 False)
    """
    admin_id = App.globalGet(ADMIN_ID)

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: app_id,
                TxnField.application_args: [
                    SET_GLOBAL,
                    module_name,
                    global_name,
                    global_value,
                    global_int,
                ],
                TxnField.applications: [admin_id],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def del_global_txn(app_id, module_name, global_name):
    admin_id = App.globalGet(ADMIN_ID)

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: app_id,
                TxnField.application_args: [DEL_GLOBAL, module_name, global_name],
                TxnField.applications: [admin_id],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def inner_asset_transaction(asset_receiver, asset_id, asset_amount):
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_amount: asset_amount,
                TxnField.asset_receiver: asset_receiver,
                TxnField.xfer_asset: asset_id,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def inner_freeze_subscription(beneficiary, asset_id):
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetFreeze,
                TxnField.freeze_asset: asset_id,
                TxnField.freeze_asset_account: beneficiary,
                TxnField.freeze_asset_frozen: Int(1),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def inner_unfreeze_subscription(beneficiary, asset_id):
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetFreeze,
                TxnField.freeze_asset: asset_id,
                TxnField.freeze_asset_account: beneficiary,
                TxnField.freeze_asset_frozen: Int(0),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def clawback_subscription(clawback_account, beneficiary, asset_id):
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.sender: clawback_account,
                TxnField.xfer_asset: asset_id,
                TxnField.asset_amount: Int(1),
                TxnField.asset_sender: beneficiary,
                TxnField.asset_receiver: clawback_account,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def _check_admin_role(beneficiary):

    admin_id = App.globalGet(ADMIN_ID)
    beneficiary_role = App.localGetEx(beneficiary, admin_id, ROLE)

    return Seq(beneficiary_role, Assert(Eq(beneficiary_role.value(), ADMIN_ROLE)))


@Subroutine(TealType.none)
def _check_owner_role():
    _sender = Txn.sender()
    admin_id = App.globalGet(ADMIN_ID)
    is_owner = App.globalGetEx(admin_id, OWNER)

    return Seq(is_owner, Assert(Eq(_sender, is_owner.value())))


@Subroutine(TealType.none)
def set_admin_local_txn(beneficiary, local_name, local_value, local_int):
    """
    beneficiary: bytes
    local_name: bytes
    local_value: bytes
    local_int: indicate if local_value is a number (1 True - 0 False)
    """
    admin_id = App.globalGet(ADMIN_ID)

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: admin_id,
                TxnField.application_args: [
                    SET_LOCAL,
                    CREATOR_POOL,
                    local_name,
                    local_value,
                    local_int,
                ],
                TxnField.accounts: [beneficiary],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def increase_asset_pool_creator(creator_pool_address, asset_id, asset_amount):
    admin_id = App.globalGet(ADMIN_ID)

    creator_pool = App.globalGetEx(admin_id, CREATOR_POOL)

    return Seq(
        creator_pool,
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: asset_id,
                TxnField.asset_receiver: creator_pool_address,
                TxnField.asset_amount: asset_amount,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_id: admin_id,
                TxnField.application_args: [INCREASE_ASSET_POOL_REWARDS],
                TxnField.applications: [
                    admin_id,
                    Txn.applications[3],
                    Txn.applications[4],
                ],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def increase_algo_pool_creator(creator_pool_address, amount):
    admin_id = App.globalGet(ADMIN_ID)

    creator_pool = App.globalGetEx(admin_id, CREATOR_POOL)

    return Seq(
        creator_pool,
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: creator_pool_address,
                TxnField.amount: amount,
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_id: creator_pool.value(),
                TxnField.application_args: [INCREASE_ALGO_POOL],
                TxnField.applications: [
                    admin_id,
                    Txn.applications[3],
                    Txn.applications[4],
                ],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )
