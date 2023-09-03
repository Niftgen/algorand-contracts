from pyteal import *
from contracts.constants import *


@Subroutine(TealType.uint64)
def set_role_checker():

    return And(
        Eq(Txn.application_args[0], SET_ROLE),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def set_verified_status_checker():

    return And(
        Eq(Txn.application_args[0], SET_VERIFIED_STATUS),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def add_module_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], ADD_MODULE),
    )


@Subroutine(TealType.uint64)
def remove_module_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], REMOVE_MODULE),
    )


@Subroutine(TealType.uint64)
def asset_optin_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(100_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].application_args[0], ASSET_OPTIN),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def assets_optin_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(200_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].application_args[0], ASSET_OPTIN),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def change_asset_manager_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], CHANGE_ASSET_MANAGER),
    )


@Subroutine(TealType.uint64)
def clawback_asset_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], CLAWBACK_ASSET),
    )


@Subroutine(TealType.uint64)
def freeze_asset_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], FREEZE_ASSET),
    )


@Subroutine(TealType.uint64)
def create_asset_app_checker():

    return And(
        Eq(Txn.application_args[0], CREATE_ASSET_APP),
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(1_400_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def change_admin_id_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], CHANGE_ADMIN_ID),
    )


@Subroutine(TealType.uint64)
def optin_admin_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(900_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], OPTIN_ADMIN),
    )


@Subroutine(TealType.uint64)
def create_auction_checker():

    return And(
        Eq(Txn.application_args[0], START_AUCTION),
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.AssetTransfer),
        Eq(Gtxn[0].asset_amount(), Int(1)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def on_bid_auction_checker():

    return And(
        Eq(Txn.application_args[0], ON_BID),
        Eq(Global.group_size(), Int(2)),
        Or(
            Eq(Gtxn[0].type_enum(), TxnType.Payment),
            Eq(Gtxn[0].type_enum(), TxnType.AssetTransfer),
        ),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def close_auction_checker():

    return And(
        Eq(Txn.application_args[0], CLOSE_AUCTION),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def revert_nft_checker():

    return And(
        Eq(Txn.application_args[0], REVERT_NFT),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def start_sell_checker():

    return And(
        Eq(Txn.application_args[0], START_SELL),
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.AssetTransfer),
        Eq(Gtxn[0].asset_amount(), Int(1)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def purchase_nft_checker():

    return And(
        Eq(Txn.application_args[0], PURCHASE_NFT),
        Eq(Global.group_size(), Int(2)),
        Or(
            Eq(Gtxn[0].type_enum(), TxnType.Payment),
            Eq(Gtxn[0].type_enum(), TxnType.AssetTransfer),
        ),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def pay_algo_checker():

    return And(
        Eq(Txn.application_args[0], PAY_ALGO),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def pay_asset_checker():

    return And(
        Eq(Txn.application_args[0], PAY_ASSET),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def set_global_checker():

    return And(
        Eq(Txn.application_args[0], SET_GLOBAL),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def del_global_checker():

    return And(
        Eq(Txn.application_args[0], DEL_GLOBAL),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def opt_in_assets_checker():

    return And(
        Eq(Txn.application_args[0], OPT_IN_ASSETS),
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(200_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def optin_niftgen_asset_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(100_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].application_args[0], ASSET_OPTIN),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def emergency_withdraw_checker():

    return And(
        Eq(Txn.application_args[0], EMERGENCY_WITHDRAW),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def increase_rewards_checker():

    return And(
        Eq(Txn.application_args[0], INCREASE_REWARDS),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def decrease_rewards_checker():

    return And(
        Eq(Txn.application_args[0], DECREASE_REWARDS),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def get_pending_rewards_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.application_args[0], GET_PENDING_REWARDS),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def create_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        # Eq(Gtxn[0].type_enum(), TxnType.Payment),
        # Eq(Gtxn[0].amount(), Int(200_000)),
        # Eq(Gtxn[0].receiver(), Global.current_application_address()),
        # Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Txn.type_enum(), TxnType.ApplicationCall),
        Eq(Txn.application_args[0], CREATE_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def subscribe_checker():

    return And(
        Eq(Global.group_size(), Int(3)),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.application_args[0], SUBSCRIBE),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Gtxn[2].application_args[0], UTILITY),
    )


@Subroutine(TealType.uint64)
def renew_checker():

    return And(
        Eq(Global.group_size(), Int(3)),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.application_args[0], RENEW_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def cancel_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Txn.application_args[0], CANCEL_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.group_index(), Int(0)),
        Eq(Gtxn[1].on_completion(), OnComplete.CloseOut),
    )


@Subroutine(TealType.uint64)
def cancel_and_refund_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Txn.application_args[0], CANCEL_AND_REFUND_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.group_index(), Int(0)),
        Eq(Gtxn[1].on_completion(), OnComplete.CloseOut),
    )


@Subroutine(TealType.uint64)
def admin_cancel_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], ADMIN_CANCEL_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def admin_cancel_and_refund_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], ADMIN_CANCEL_AND_REFUND_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def freeze_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], FREEZE_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def unfreeze_subscription_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], UNFREEZE_SUBSCRIPTION),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def deploy_creator_app_checker():

    return And(
        Eq(Txn.application_args[0], DEPLOY_CREATOR_APP),
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(3_440_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Txn.group_index(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def withdraw_algos_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], WITHDRAW_ALGOS),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def withdraw_tokens_checker():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], WITHDRAW_TOKENS),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def utility_checker():

    return And(
        Eq(Txn.application_args[0], UTILITY),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def deploy_subscription_app_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].amount(), Int(660_000)),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], DEPLOY_SUBSCRIPTION_APP),
    )


@Subroutine(TealType.uint64)
def increase_asset_pool_rewards_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.AssetTransfer),
        Eq(Gtxn[0].asset_receiver(), Global.current_application_address()),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], INCREASE_ASSET_POOL_REWARDS),
    )


@Subroutine(TealType.uint64)
def increase_pool_rewards_checker():

    return And(
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Global.current_application_address()),
        Eq(Gtxn[0].sender(), Gtxn[1].sender()),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.application_args[0], INCREASE_ALGO_POOL),
    )


@Subroutine(TealType.uint64)
def calculate_asset_rewards_checkers():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], CALCULATE_ASSET_REWARDS),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def calculate_algo_rewards_checkers():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], CALCULATE_ALGO_REWARDS),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def withdraw_asset_reward_checkers():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], WITHDRAW_ASSET),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def withdraw_algo_reward_checkers():

    return And(
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args[0], WITHDRAW_ALGO),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def set_local_checker():

    return And(
        Eq(Txn.application_args[0], SET_LOCAL),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )


@Subroutine(TealType.uint64)
def change_ownership_checker():

    return And(
        Eq(Txn.application_args[0], CHANGE_OWNERSHIP),
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
    )
