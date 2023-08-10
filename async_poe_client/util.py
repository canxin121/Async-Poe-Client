import json
import random
import re
import secrets
import uuid

import quickjs
from loguru import logger

CONST_NAMESPACE = uuid.UUID("12345678123456781234567812345678")

QUERIES = {
    "AddEmailMutation": "6d9ff3c8ed7badced30cfdad97492d4c21719931e8c44c5601abfa429b62ded7",
    "AddMessageBreakEdgeMutation": "9450e06185f46531eca3e650c26fa8524f876924d1a8e9a3fb322305044bdac3",
    "AddPhoneNumber": "26ae865f0686a910a86759c069eb1c0085d78b55a8abf64444ec63b03c76fb58",
    "AnnotateWithIdsProviderQuery": "b4e6992c3af8f208ab2b3979dce48889835736ed29f623ea9f609265018d0d8f",
    "AvailableBotsListModalPaginationQuery": "3be373baa573ccd196b9d71c94953b1d1bc586625bd64efe51655d75e68bbfb7",
    "AvailableBotsSelectorModalPaginationQuery": "cb23667c6c2a13501275d0e958e54e705da6f361dd90a0166994c18b20ec8965",
    "BotInfoFormRunCheckMutation": "87d55551061151b852fd7c53ec34dbb1ae784516b0ba2df5255b201f0d4e1444",
    "BotInfoModalQuery": "d84c9e2fb3d698edb3c82b9eeca9ceee08ba6461a19bfcfd971f5c60c2dd9012",
    "BotLandingPageQuery": "f77b0d0e1a14a7d8a8c84398c146a4d721efd1f7a2ff911bf6d7b27d3341c14c",
    "BotSelectorModalQuery": "95e4c0fec4247d24a2c4c2eb6aa87845fca627e53254a133e964ba5c2e4fb6e0",
    "BotSwitcherModalQuery": "54023ee8b691543982b2819491532532c317b899918e049617928137c26d47f5",
    "ChatDeleteConfirmationModalQuery": "d697a075bcc5a027db5fe5777c9434053210a81c4e29f6f4380de1b21bd3f8c3",
    "ChatHelpersSendNewChatMessageMutation": "c11a9745cf18811287e03fc81e766fbeeaa6c65cbf4e54648f7400ee09f90ebc",
    "ChatHistoryFilteredListPaginationQuery": "7aeedfea3592a32ae1870f854eb713587b0d0fa7cfbaf8c1d19271d7f2773e4f",
    "ChatHistoryListPaginationQuery": "dd949d5d1497f1456587a3836eab106c0a0726c8e253dd2acfb3fa178a3f6a3f",
    "ChatListPaginationQuery": "8e36816f3aa12b6d5508cfca1cc44c5128d5df0405cfbdf01cfd1b666354db1f",
    "ChatPageBotBotsPagination": "ed9017f85fe2fedbf02b2d000cb4b551d2ec870715d0c7bce6d54a0f3f9b657b",
    "ChatPageQuery": "85e6209451ddf1bc7d019eb73fb9b7072689aadb85b1a75f60a56185861286c7",
    "ChatSetTitle": "4b499ec70041141714a0ba1ae8ab6c9595d73845735715a7d4b86ae679a87696",
    "ChatSettingsModalQuery": "5e8357fd21ed24988015b2cb9ca0bffee6512740d403ead43ea46605059180e7",
    "ChatSubscriptionPaywallModalQuery": "1cba8b9a13ffa600c7b3a02ad0c1a7f1609b8f877d56d3b8517db2bb0d1294bb",
    "ChatTitleUpdated": "59a6bb3b783e392aaa18ed2baf3a3be65605a7e4760e1c9c687e217e3446127c",
    "ChatsHistoryPageQuery": "d1c0dd48f6ffd960c95995a92c899859e35b82e687d915d2510f89a22d944633",
    "ContinueChatFromPoeShare": "da387c7cce806a5a0820d31314eb77ea16c8b78d740d94a3aee26823afad467a",
    "ContinueChatIndexPageQuery": "a7eea6eebd14aa355723514558762315d0b4df46205b70f825d288d5ed1635ec",
    "ContinueChatPageQuery": "fe3a4d2006b1c4bb47ac6dea0639bc9128ad983cf37cbc0006c33efab372a19d",
    "CreateBotIndexPageQuery": "6bd24eb031dd0d427ddeef0c4113d9b3800aa44b62aed25143d6a95251765e38",
    "CreateBotPageQuery": "4fa5e0703c416fc6b40c5e2fcfcac66301ed0c8d32bafb5d69300e7553ef1f8f",
    "CreateChatMutation": "a55432622aaaf7f7277ab12f07725a0c88c5ca36434c909208973189c4c7aa24",
    "CreateChatWithTitle": "ccede193610b2b0243192ad2fc13cadc3f8103b6439b7920da1ca643f109243e",
    "CreateCheckoutSession": "5eb43e7c83974acc6680e1abe4c169296d0b346c42cc20d487762163402ea8e5",
    "CreateCustomerPortalSession": "4d43136f33aba6b6dea2ac8cd295e03bd841b7c99bf772940fa06a623a331786",
    "CreateMessagesToContinueChatMutation": "00b66f0117fab1ab6cdcf7e98819c1e3196736253b6a158316a49f587b964d25",
    "DeleteAccountMutation": "4e9651277464843d4d42fbfb5b4ccb1c348e3efe090d6971fa7a3c2cabc7ea5c",
    "DeleteChat": "5df4cb75c0c06e086b8949890b1871a9f8b9e431a930d5894d08ca86e9260a18",
    "DeleteMessageMutation": "8d1879c2e851ba163badb6065561183600fc1b9de99fc8b48b654eb65af92bed",
    "DeleteUserMessagesMutation": "3f60d527c3f636f308b3a26fc3a0012be34ea1a201e47a774b4513d8a1ba8912",
    "DismissDismissible": "b133084411c0a7a2353f6cfacd3d115260c34ddc5d97cf7f19a16e8cb4410803",
    "EditBotIndexPageQuery": "52c3db81cca5f44ae4de3705633488511bf7baa773c3fe2cb16b148f5b5cf55e",
    "EditBotPageQuery": "67c96902edcb66854106892671c816d9f7c3d8910f5a6b364f8b9f3c2bc7a37a",
    "EmailUnsubscribe": "eacf2ae89b7a30460619ccfb0d5a4e6007cfbcf0286ec7684c24192527a00263",
    "EmbedLoggedOutPageQuery": "e81580f4126215186e8a5d18bdedcf7c056b634d4d864f54b948765c8c21aef9",
    "ExploreBotsCarouselContainerQuery": "80c1bd803ee711eb68d76396aca794da2c57156adaed5ce3307882af7bb7cdaf",
    "ExploreBotsCarouselLazyLoadedContainerQuery": "8041cd32aa1e73e1d82fcb0f7b8b758b5201a032153fb1e96b0d9f8dee029a8a",
    "ExploreBotsCarouselPagedContainerPaginationQuery": "6a159c606fade78cfa8a1164290a822361f7d24ce16b07bca66ab19b24a639ce",
    "ExploreBotsIndexPageQuery": "5b1e4a5bc7b213e43e16dd1b8d0823853fb8006806a3ee9e2070fffc33b30b57",
    "ExploreBotsListPaginationQuery": "983be13fda71b7926b77f461ae7e8925c4e696cdd578fbfd42cb0d14103993ac",
    "ExploreBotsPageQuery": "170190a4ef153475c9b7cdcc7780d6f120e1402cc0bf239e23414db2bb2838d1",
    "ExploreBotsSidebarQuery": "00f42e3842c63cfcfcebad6402cdaa1df1c3fa7ffe3efbe0437a08a151eca87e",
    "GenerateAppleAuthNonceMutation": "c3e0c1b990cd17322716d0fa943a8ddc0ffecf45294ad013ccc883954c2171fc",
    "HandleBotChatEmbedPageQuery": "399775041662f58cd339ffb60895f45601c83f4f688e1e8aeaf36396f40466fd",
    "HandleBotChatPageQuery": "6008bbe2fd26c9799a4e0ecb758ee55b6935270839a628383d35177eb16e8bbc",
    "HandleProfileIndexPageQuery": "0243e1784c33ae913d8a3ad20fc1252b930b6741ff9d78bd776e2df4f93f55ee",
    "HandleProfilePageQuery": "4605a49a28aa5647b96f437d61a8b9318e2619d9974c61759b0ec82b201befb7",
    "IntroMainQuery": "47f2c9bb41be5238968c81c82f2d2cff4100c73fcc70a9f592825bb40c0efc8d",
    "LayoutLeftSidebarQuery": "6c1c2fef7e2da327140c0a84b752915d410c31c38dd84136537255dba68697fa",
    "LayoutRightSidebarQuery": "71a5fc350dd717477e1ab28426879dcf2531e67df71283fe15d3bfe4889e6a23",
    "LoginPageQuery": "2599cb7b73e689206ae0e28902d743eacae29cef1198d2b3c491c414227e295e",
    "LoginWithVerificationCodeMutation": "0d5aecd57239d518c25dc972569ee77dd9610a114610a6a3e87b87fdd8f1ba90",
    "LogoutAllSessionsMutation": "1e62b26302959ca753def8678e817b2c1ad94efdb21872dbf0f8bffcb892aed4",
    "LogoutMutation": "1d2e52b19e15a6aa0ec93d8e4a3a9653b9ceb4c1f365c7d9c4451d835505eef2",
    "MarkAndroidAppDownloadPromptSeen": "ed6891c8913983cc4fd0bfed9760e9738743419712ce6681841217ed0bb8c915",
    "MarkMultiplayerNuxCompleted": "c1b1f2ce72d9f8e9cd7bbe1eecbf6e3bed3366df6a18b179b07ddfd9f1f8b3b1",
    "MessageAdded": "343d50a327e93b9104af175f1320fe157a377f1dbb33eaeb18c6a95a11d1b512",
    "MessageCancel": "59b10f19930cf95d3120612e72d271e3346a7fc9599e47183a593a05b68c617e",
    "MessageCancelled": "dfcedd9e0304629c22929725ff6544e1cb32c8f20b0c3fd54d966103ccbcf9d3",
    "MessageDeleted": "91f1ea046d2f3e21dabb3131898ec3c597cb879aa270ad780e8fdd687cde02a3",
    "MessageLimitUpdated": "38a2aada35e6cf3c47d9062c84533373cad2ec9205b37919a4ba8e5386115a17",
    "MessageUnvoteMutation": "af2b91f09ab2ccf53ba9176a86b9934b98a865adf228b2ac3a548d6397f382f3",
    "MessageVoteMutation": "07458e93fab951a4127f7c69743269a0d21c00ed2fdf593cba2aa8050c09a760",
    "NewLandingPageQuery": "003af54e7fdde83cb0118a405a079085073b3aee3b8d2111a138f3b6e2958b71",
    "NumTokensFromPromptQuery": "1d9bef79811f3b2ddca5ce4027b7eaa31a51bbeed1edf8b6f72e2e0d09d80609",
    "NuxInitialModalQuery": "f8cd0d8494afe3b5dbb349baa28d3ac21f2219ce699e2d59a2345c864905e0c3",
    "OnboardingBestOfPoeModalQuery": "d144c16d74fd85eeeae43331109dcd3fc86f8956e580f740cf4d239a0029c225",
    "OnboardingSubscribeImageModalQuery": "468a5303bca4d4a4fa03ebc3d4fe49138fc9151257661570f40dd0eac82b03ca",
    "OnboardingSubscribeModalQuery": "f766345663b0b26d23c70525c2a7209468245164c2459fde26c36c798bff6f9a",
    "OptimisticChatLoaderQuery": "2bbb2b9b1878d56cde5cac5a37019373d7e8230cf8367436563acd3d9ba60c13",
    "PageBlockerQuery": "d1ab792fce4d3f91777b49856d44b2d9cbb6ad1231e1116c407a0208604181e1",
    "PagesBotNameQuery": "a156136af92b189768540f864445f0b8d9191584530def6b1a5502c843539cfb",
    "PagesDefaultBotChatPageQuery": "27a2fb791e8e680f2ad8966b181fb4abbff333654ab138cf39a4607ec6c3c82d",
    "PoeBotCreate": "fcc424e9f56e141a2f6386b00ea102be2c83f71121bd3f4aead1131659413290",
    "PoeBotDelete": "c5e5ee2fdac007b02d074ce7882a0631bfbccc73d8833ba8765297c5ea782bb6",
    "PoeBotEdit": "eb93047f1b631df35bd446e0e03555fcc61c8ad83d54047770cd4c2c418f8187",
    "PoeBotFollow": "efa3f25f6cd67f9dea757be50305c0caa6a4e51f52ffba7e4a1c1f2c84d6dbd0",
    "PoeBotUnfollow": "db2281f3efa305db62d38964b640e982076491c2c59d5be3303feae343fe8914",
    "PoeRemoveBotFromUserList": "89e756b668b2318fa73c2a9dde4608a4529c74844667417c0cfb245e7e04e96e",
    "PoeSetBio": "66fb99ec59fa17bc4487f944d116bc920161faced58a3ce99e82cb61af61468e",
    "PoeSetHandle": "b57a53d5ae7a881e81616c0dd70e7b9d1d9ba4118a9969653cadc6284d89cf7f",
    "PoeSetName": "c406a46fe6ff244ab2d665ea953fc8655d6816f1731505d830863d9b9c5021bf",
    "PoeSetProfilePhoto": "13106f2433e5d48a53e6804b76022e80c0fc9bf018eb5b5404d9e0a4acd94f1f",
    "PoeUserSetFollow": "dcc26e4e36b47af8af6bd0296ff85dfa8fc77a9c374ea5989afd0bf39ae4d35e",
    "PostIdPostPageQuery": "28f6a6063fddab39b5f9e9af8cd3208163eafbe2c8bb998ae61f0da55134de6a",
    "ProfileIndexPageQuery": "4044ca7eb203e613f19dc76a4a05ca1df25bfdb2ff761a9d6dced6b0d61f219a",
    "ProfilePageQuery": "9505daf59f885463e5bd3bb2a1a9fc088e8634fbc7d5a0682f2ece11ee7548dd",
    "RemoveEmailMutation": "63750a7e41cc0ad3f6da0be1fdae9c243f1afab83cf44bb5c3df14243074681d",
    "RemoveUserPhoneNumberMutation": "7dadad6ac75a8a4e5c54479524c7821e748c043242476958262bb39fa60ccddb",
    "SaveContinueChatInfoMutation": "ae56678376401ae45dbba61aa6b1a55564877edc33605db6283e1dc3bdb0c8ff",
    "SearchResultsListPaginationQuery": "03ce30a457ef8fed9f7677ed642eed8eadd86ca1c7c034f69cb16feb79f5fad2",
    "SearchResultsMainQuery": "b904ab9c97ee1535c1b9b2fa1851b7735f7b4638e535c3230d2a0e235bc78024",
    "SelectorTestPageQuery": "9ec86fe8e3d0d3b264d0fab0feb73e38c86d616c7c3d8340d7a6146bd8445ed3",
    "SendMessageMutation": "5fd489242adf25bf399a95c6b16de9665e521b76618a97621167ae5e11e4bce4",
    "SendVerificationCodeMutation": "1b3d5a8c7fd8b187b14552d3d1ab13b19d5ea263e9716a207fedc23853c0b98a",
    "SetPrimaryEmailMutation": "01e75a6d937351b304ca9cc0b231e43587a5923e7f8618863bdf996df38d28b5",
    "SettingsDefaultBotSectionMutation": "4084604e8741af8650ac6b4236cdfa13c91a70cf1c63ad8a368706a386d0887e",
    "SettingsIndexPageQuery": "50722a6de168bf92d20b00674c981cd5450f88d62348f51076fce32a0898c965",
    "SettingsPageQuery": "fb6399e5fbefb4a2c493381aa5f93c8d306f6dd3aa30a363d07799c4ad645830",
    "ShareCodeSharePageQuery": "689890279054b2a76d6fa6dd63267df03242ae6db39c3d8508f9642ed37a8dc9",
    "ShareMessageMutation": "2491190f42c1f5265d8dbaaaf7220dbfa094044fdfb2429fd7f2e35f863bc5e1",
    "SignupOrLoginWithAppleMutation": "074bf2533767ae06ced2046b538299b0ca7d8934da22ce6b7de51b666ffbfa30",
    "SignupOrLoginWithGoogleMutation": "253e1f712eff09e801f6cf85140b400e7b949d27b5d410c803d69ce7cf65131b",
    "SignupOrLoginWithQuoraMutation": "ee2498e8837e7b975806613401f5aa4ba18d03fdcc9fde0c59efc75717103df5",
    "SignupWallModalInnerQuery": "d70ff1ffe0efe1fe0f92e73e50e6b703e4f790225abcefe3067a32d9da7f7c32",
    "SignupWithVerificationCodeMutation": "9d6dcfd41abc43c13010988224ae680fa6b09733d990a4b5393a78124481d94a",
    "StaticContentQuery": "15267bf130fbe298a6f60334f57ccf62bc16ff06c74d5778ba54b4b4f21f8d0c",
    "SubscriptionTosQuery": "c3bf58b2f81083b0def2f51b4fec2a2e2a5e7abe1c7df635f3efeb7b44469f8a",
    "SubscriptionsMutation": "61c1bfa1ba167fd0857e3f6eaf9699e847e6c3b09d69926b12b5390076fe36e6",
    "UniversalLinkPageQuery": "ec7c629dd6ec79f9d26dda9c4ef9cb1e24aa41d7b92090596b6639eeee5e6cc8",
    "UpdatePhoneNumber": "c49f5f64947c2946f8007f366bbc0ca5b1f0bbbdc6b72ad97be90533f0e83c28",
    "UseBotSelectorViewerBotsPaginationQuery": "97fdae8981da0b3528df63b86f303378abf0320341866905e6cba500b5e0db96",
    "UseStopMessageAndSendChatBreak": "9b95c61cd6cb41230a51fb360896454dde1ae6d1edb6f075504cb83a52422bc9",
    "UserEditBioModalQuery": "b78089f19d1071ad9440d5a2696588b0e82a012f6b40dca68f071cc0a49727f2",
    "UserEditHandleModalQuery": "ecee1f772c401f6e429ba7ebe088eedc0aa6d24dfa4cae0ec6f54bb3c5a5c653",
    "UserEditNameModalQuery": "dd72d69698a46097386b73b19677a84b6bcba51b3df3790e67d804b6da686787",
    "UserEditProfilePicModalQuery": "7f69ff6407a1360570863b09a9c02bf0a4bdbd8de2b04e5dde4eec031a6f62e5",
    "UserFolloweesListModalQuery": "b219f7e8b7c8d21aaa0979d44bfc3935501719e3fe18cbe86b459eced5f290d2",
    "UserFollowersListModalQuery": "86b007fa15b2de6f7eb527050832d342dde837aaedfb61bfdd1bf1201b860b61",
    "UserProfileConfigurePreviewModalQuery": "abec61f90eebcc3b914487db0ba35ff6ec53c1f7c29f40f59222cee5b8832a52",
    "ViewerStateUpdated": "ee640951b5670b559d00b6928e20e4ac29e33d225237f5bdfcb043155f16ef54",
    "WebSpeedUpsellQuery": "d8556da659d21dc2c583248c1c617ca20492b64c6948ae4a16256c0848f9c32e",
    "WebSubscriptionPaywallModalQuery": "dedc399e9fa52dc43c05bd183032c541fa655690222e37a7cf2dbb37cf46c365",
    "WebSubscriptionPaywallWrapperQuery": "210dc63dc4b2bfba2e0a4a1288013097cc920f3a26e9988cb191836541d26458"
}
GQL_URL = "https://poe.com/api/gql_POST"
GQL_RECV_URL = "https://poe.com/api/receive_POST"
HOME_URL = "https://poe.com"
SETTING_URL = "https://poe.com/api/settings"


def generate_data(query_name, variables) -> str:
    if query_name == "recv":
        data = [
            {
                "category": "poe/bot_response_speed",
                "data": variables,
            }
        ]
        if random.random() > 0.9:
            data.append(
                {
                    "category": "poe/statsd_event",
                    "data": {
                        "key": "poe.speed.web_vitals.INP",
                        "value": random.randint(100, 125),
                        "category": "time",
                        "path": "/[handle]",
                        "extra_data": {},
                    },
                }
            )
    else:
        data = {
            "extensions": {
                "hash": QUERIES[query_name]
            },
            "queryName": query_name,
            "variables": variables,
        }
    return json.dumps(data, separators=(",", ":"))


def generate_nonce(length: int = 16):
    return secrets.token_hex(length // 2)


def extract_formkey(html, script):
    """can't use, 'document' is not defined"""
    script_regex = r'<script>(.+?)</script>'
    vars_regex = r'window\._([a-zA-Z0-9]{10})="([a-zA-Z0-9]{10})"'
    key, value = re.findall(vars_regex, script)[0]

    script_text = """
      let QuickJS = undefined, process = undefined;
      let window = {
        document: {a:1},
        navigator: {
          userAgent: "a"
        }
      };
    """
    script_text += f"window._{key} = '{value}';"
    script_text += "".join(re.findall(script_regex, html))

    function_regex = r'(window\.[a-zA-Z0-9]{17})=function'
    function_text = re.search(function_regex, script_text).group(1)
    script_text += f"{function_text}();"

    context = quickjs.Context()
    formkey = context.eval(script_text)

    salt = None
    try:
        salt_function_regex = r'function (.)\(_0x[0-9a-f]{6},_0x[0-9a-f]{6},_0x[0-9a-f]{6}\)'
        salt_function = re.search(salt_function_regex, script_text).group(1)
        salt_script = f"{salt_function}(a=>a, '', '');"
        salt = context.eval(salt_script)
    except Exception as e:
        logger.warning("Failed to obtain poe-tag-id salt: " + str(e))

    return formkey, salt
