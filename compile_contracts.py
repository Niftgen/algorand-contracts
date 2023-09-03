from contracts.modules.auction import auction_approval, auction_clear
from contracts.modules.list import list_approval, list_clear
from contracts.modules.creator_app import (
    creator_app_approval,
    creator_app_clear,
)
from contracts.modules.nft_app import nft_app_approval, nft_app_clear
from contracts.admin import admin_approval, admin_clear
from contracts.modules.rewards_module import (
    rewards_module_approval,
    rewards_module_clear,
)
from contracts.modules.subscription_module import (
    subscription_module_approval,
    subscription_module_clear,
)
from contracts.modules.subscription_app import (
    subscription_app_approval,
    subscription_app_clear,
)
from contracts.creator_pool.creator_pool import (
    creator_pool_approval,
    creator_pool_clear,
)

from algosdk.v2client import algod

client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")

def compile_auction():
    print("Compiling auction teal...")

    approval_program = auction_approval()
    approval = open("./compiled_contract/auction_approval.teal", "w")
    approval.write(approval_program)

    clear_program = auction_clear()
    clear = open("./compiled_contract/auction_clear.teal", "w")
    clear.write(clear_program)

    print("Compiled auction teal!\n")


def compile_list():
    print("Compiling list teal...")

    approval_program = list_approval()
    approval = open("./compiled_contract/list_approval.teal", "w")
    approval.write(approval_program)

    clear_program = list_clear()
    clear = open("./compiled_contract/list_clear.teal", "w")
    clear.write(clear_program)

    print("Compiled list teal!\n")


def compile_nft_app():
    print("Compiling nft app teal...")

    approval_program = nft_app_approval()
    approval = open("./compiled_contract/nft_app_approval.teal", "w")
    approval.write(approval_program)

    clear_program = nft_app_clear()
    clear = open("./compiled_contract/nft_app_clear.teal", "w")
    clear.write(clear_program)

    print("Compiled nft app teal!\n")


def compile_admin():
    print("Compiling admin app teal...")

    approval_program = admin_approval()
    approval = open("./compiled_contract/admin_approval.teal", "w")
    approval.write(approval_program)

    clear_program = admin_clear()
    clear = open("./compiled_contract/admin_clear.teal", "w")
    clear.write(clear_program)
    print("Compiled admin app teal!\n")


def compile_creator_app():
    print("Compiling creator deployer module teal...")
    nft_app_approval_compile_response = client.compile(nft_app_approval())
    nft_app_approval_program = nft_app_approval_compile_response["result"]
    nft_app_clear_compile_response = client.compile(nft_app_clear())
    nft_app_clear_program = nft_app_clear_compile_response["result"]

    approval_program = creator_app_approval(
        nft_app_approval_program, nft_app_clear_program
    )
    approval = open("./compiled_contract/creator_app_approval.teal", "w")
    approval.write(approval_program)

    clear_program = creator_app_clear()
    clear = open("./compiled_contract/creator_app_clear.teal", "w")
    clear.write(clear_program)
    print("Compiled creator deployer module teal!\n")


def compile_rewards():
    print("Compiling rewards module...")
    approval_program = rewards_module_approval()
    approval = open("./compiled_contract/rewards_module_approval.teal", "w")
    approval.write(approval_program)

    clear_program = rewards_module_clear()
    clear = open("./compiled_contract/rewards_module_clear.teal", "w")
    clear.write(clear_program)
    print("Compiled rewards module!\n")


def compile_subscription_module():
    print("Compiling subscription module...")
    subscription_app_approval_compiled = client.compile(subscription_app_approval())
    subscription_app_approval_program = subscription_app_approval_compiled["result"]

    subscription_app_clear_compiled = client.compile(subscription_app_clear())
    subscription_app_clear_program = subscription_app_clear_compiled["result"]

    approval_program = subscription_module_approval(
        subscription_app_approval_program, subscription_app_clear_program
    )
    approval = open("./compiled_contract/subscription_module_approval.teal", "w")
    approval.write(approval_program)

    clear_program = subscription_module_clear()
    clear = open("./compiled_contract/subscription_module_clear.teal", "w")
    clear.write(clear_program)
    print("Compiled subscription module!\n")


def compile_subscription_app():
    print("Compiling subscription app...")
    approval_program = subscription_app_approval()
    approval = open("./compiled_contract/subscription_app_approval.teal", "w")
    approval.write(approval_program)

    clear_program = subscription_app_clear()
    clear = open("./compiled_contract/subscription_app_clear.teal", "w")
    clear.write(clear_program)
    print("Compiled subscription app!\n")


def compile_creator_pool():
    print("Compiling creator pool app...")
    approval_program = creator_pool_approval()
    approval = open("./compiled_contract/creator_pool_approval.teal", "w")
    approval.write(approval_program)

    clear_program = creator_pool_clear()
    clear = open("./compiled_contract/creator_pool_clear.teal", "w")
    clear.write(clear_program)
    print("Compiled creator pool app!\n")


if __name__ == "__main__":
    compile_auction()
    compile_list()
    compile_nft_app()
    compile_admin()
    compile_creator_app()
    compile_rewards()
    compile_subscription_app()
    compile_subscription_module()
    compile_creator_pool()
