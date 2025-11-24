"""
诺亚CRM产品代码与productId映射关系
从用户提供的链接中提取
"""

# 产品代码到诺亚CRM productId的映射
NOAH_PRODUCT_MAPPING = {
    "L01485": "819a4a8368fc4cc89195bb37d8034755",
    "L01615": "21a0326bbc054b2ba85c23b64023f648",
    "L01728": "03afc572822140acae4bb8a0feaeb8c3",
    "L01777": "d0349c85653740dd9e7d08a00b6e731b",
    "L01810": "02c3f3914fe34c4d8341e7b792dbd3c6",
    "L01863": "9bedcebb7b4148a5afa9962d3c9eada1",
    "L01896": "5f7873f17e7f4bdbab2adc2c7b6d81e7",
    "L01997": "3f3e8662642047bebaed2343e1651a99",
    "L02053": "9236c207af42455bb7c528560ea1836d",
    "L02085": "bccab441bca24d33a0eec49e56ee4f23",
    "L02103": "db1967951a424df991316699168a2100",
    "L02241": "fa13ad70524f48919123545414c46a75",
    "L02280": "ca0f2ce559a3446db52e3d28374b7330",
    "L02373": "fbbdfad8f1764a5cb8faf1cf8388cc74",
    "L02376": "ebec43833f3a49c495a8cae45e21a6e0",
    "L02510": "8fc847ea42c94e8f852847e28ee5080e",
    "L02512": "3c187212f1874202ad8a881128c55c39",
    "L02533": "e659b8165c3545418f8f4e5da094444c",
    "L02541": "58bef4513d2d4506a4c3628cc70b67f5",
    "L02544": "88f510e807694d36a955ebefda39c19f",
    "L02546": "4750a0b7f6924915b448614868a7d171",
    "L02555": "22e307a2d66d4011b7a2c20ba4f15317",
    "L02612": "f8c314d50d77416b9e8bcb5df4840246",
    "L02617": "300f839299224441a9d0dd90bd108a58",
    "L02643": "3242d7ebee61415ab4a6336b7b0b807c",
    "L02659": "61f54801b34846d79c2227f077ac9eda",
    "L02660": "5b6aff039e7848faa8ff804eb1c68e7a",
    "L02668": "65b8902c935a4d259215ef987d4f452d",
    "L02669": "a877368b2e3f4ad082516a877d2583f0",
    "L02697": "2a19e875866c4c57b962ed2fb6c95d6a",
    "L02709": "0cc1dac5a9b84c02bdefe18e2ec8328d",
    "L02712": "c74abb3d1a6b4b4bbbffdb4e6007a14c",
    "L02724": "19b16c14787241b7ade19fcc88558ed1",
    "L02775": "c51bd996a08b4956b28b71326d076dcf",
    "L02793": "8182eeb264634e52a671d346d28e2ca3",
    "L02796": "bf3c8609d236492f8b50ea8cdb518baf",
    "L02798": "4e2e1f0469c344c9a0aa72ad126848ce",
    "L02851": "74cbf63d1e0c4451ae622008e7490f47",
    "L02853": "9b558519dee442cba30a6970e1d144fa",
    "L02884": "a6069b889e674b2598aa22aca38b80f4",
    "L02900": "0f50fd19c89541b698756858d5cee66a",
    "L02909": "25afea54d545433fb4641e33886d7f8f",
    "L02942": "f2f4418a4b474dbea3abb015e01c0c73",
    "L02958": "ac1a201d712c414f99f74e2712674c4f",
    "L03018": "66bfa98c9a6f4b81b5add7066d254ea3",
    "L03035": "1c9ee73afc36463ca1383c8bcd502078",
    "L03049": "f763cb297e394d3888a506cb128d0f1b",
    "L03092": "cfa9c90ee4a6486cbcbecdca19528221",
    "L03096": "a5f4114fc92e4399adbe91bc6bf2cf6e",
    "L03099": "d6a9b4caaff34bada3c0f255b6380cf1",
    "L03100": "f2ad8fae7bfd48e8a22dc347879e8ecc",
    "L03120": "e5b815c3da9a4aa4b74474748daedf0f",
    "L03143": "28ff718cdea2476ea237cc60b0587a17",
    "X01130": "98d19d8085034034b8b8cfef8c2fbe6d",
}


def get_noah_product_id(fund_code: str) -> str:
    """根据产品代码获取诺亚CRM的productId"""
    return NOAH_PRODUCT_MAPPING.get(fund_code)


def get_all_mapped_funds():
    """获取所有已配置映射的产品代码"""
    return list(NOAH_PRODUCT_MAPPING.keys())
