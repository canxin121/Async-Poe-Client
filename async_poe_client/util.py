import json
import secrets
import uuid

CONST_NAMESPACE = uuid.UUID("12345678123456781234567812345678")

QUERIES = {
    "chatHelpersSendNewChatMessageMutation": "943e16d73c3582759fa112842ef050e85d6f0048048862717ba861c828ef3f82",
    "chatHelpers_sendMessageMutation_Mutation": "5fd489242adf25bf399a95c6b16de9665e521b76618a97621167ae5e11e4bce4",
    "ChatPageQuery": "63eee0aafc4d83a50fe7ceaec1853b191ea86b3d561268fa7aad24c69bb891d9",
    "ExploreBotsListPaginationQuery": "983be13fda71b7926b77f461ae7e8925c4e696cdd578fbfd42cb0d14103993ac",
    "BotLandingPageQuery": "fb2f3e506be25ff8ba658bf55cd2228dec374855b6758ec406f0d1274bf5588d",
    "chatsHistoryPageQuery": "050767d78f19014e99493016ab2b708b619c7c044eebd838347cf259f0f2aefb",
    "availableBotsSelectorModalPaginationQuery": "dd9281852c9a4d9d598f5a215e0143a8f76972c08e84053793567f7a76572593",
    "chatHelpers_addMessageBreakEdgeMutation_Mutation": "9450e06185f46531eca3e650c26fa8524f876924d1a8e9a3fb322305044bdac3",
    "subscriptionsMutation": "5a7bfc9ce3b4e456cd05a537cfa27096f08417593b8d9b53f57587f3b7b63e99",
    "BotInfoCardActionBar_poeBotDelete_Mutation": "ddda605feb83223640499942fac70c440d6767d48d8ff1a26543f37c9bb89c68",
    "CreateBotMain_poeBotCreate_Mutation": "fcc424e9f56e141a2f6386b00ea102be2c83f71121bd3f4aead1131659413290",
    "EditBotMain_poeBotEdit_Mutation": "eb93047f1b631df35bd446e0e03555fcc61c8ad83d54047770cd4c2c418f8187",
    "editBotIndexPageQuery": "52c3db81cca5f44ae4de3705633488511bf7baa773c3fe2cb16b148f5b5cf55e",
    "BotInfoCardActionBar_poeRemoveBotFromUserList_Mutation": "94f91aa5973c4eb74b9565a2695e422a2ff2afd334c7979fe6da655f4a430d85",
    "useDeleteChat_deleteChat_Mutation": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",
    "ChatListPaginationQuery": "dc3f4d34f13ed0a22b0dbfa6a1924a18922f7fe3a392b059b0c8c2134ce4ec8a"
}
GQL_URL = "https://poe.com/api/gql_POST"
HOME_URL = "https://poe.com"
SETTING_URL = "https://poe.com/api/settings"


def generate_data(query_name, variables) -> str:
    data = {
        "queryName": query_name,
        "variables": variables,
        "extensions": {
            "hash": QUERIES[query_name]
        }
    }
    return json.dumps(data, separators=(",", ":"))


def generate_nonce(length: int = 16):
    return secrets.token_hex(length // 2)
