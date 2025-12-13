import json
import time

# Tokens from your debug output
manual_data = {
    "access_token": "pUBHeNWduwVYnt4W56VkCJZNuBJnfRnOllsiZPh9Xs0jWM4Toa6hwlaJndr0Gw7mV3cl97UlMYz.g5B4crEA6vnrDY04iZVnh3ud0YIRXD4TNcUyPOR6uR88C4MwYmXQ9r7yFm_pvWZJu6KSac_iQzHm3eoSli9LCIeEp78DoA.JiXzoZx5KpehNBv4jU4B1sTLIydp6UrWKSFclF7JjcwFLO1iZASe0fdrqbfAvpzTucQNDnixIYQly7o1Rupd99DcH6C8zNElPJXKTDJOkoGReQeBLOBoygDFZDCRMfDDx5aIc.lkSlDdLER6LmMLd6CkuW9cb4LAJS0.dL0ywXhl8e5.ASTRPo0UW9jUNLipIggvkSPZBjr0yX3Z___5oWPoijz.Q8i5NI2qaF6pNBRZgxlesU3hmfkS5f57BBFrjZNVy6xu9pmfTKJh3Qusx38WfCBY9WYoOQow3yiuF.2GMhdXYxkPc_hDiEZj0HcY0wJQ_MkhCLvhYn88FUeqVLpBiGgqBK1.xF046WQLQzyXyB1k3.hkg5bdSkDxNTtzE9YnHjl77Ril6.dQNvlnk8ARclzVBZSNIRAp_jECuA3RKg.j91tZ4sEN9hjme0hvdZl5NqdMfj4he6eBRJSDRTr_dBKwxE4B4TzR6_ilRi73KFYOJKVhQRwUp5a35D9kuJ7SUdPORwMzsnRZkf2xkQPSVzaPIp9_TQvJTjXmV_G0V4fg4RHRhKJjCu4umnsaGNiE2tknHy2KPuzsOfrLpmswZql6C.8YSYqXUqu0fxylRBONY0dam_cft1hJXoTjgKVpdXDXHd53MNoYwqPTy94dMx96W_uP2dfNX8mWLwWECTYPX6GqueJpPhIG58tVrazukP8TR8x6EOcHZh7ghRo0oW8RxONbMq45Aw0wEH4WJkBPJpF4Dn8ueS6Jc47WyOi.uJ.Y-",
    "refresh_token": "AB9ANmkapYWjAilTFb0N949tynfC~001~LMaeFKT80EEftcmm1NPG6N62EQ--",
    "expires_in": 3600,
    "token_type": "bearer",
    "token_time": time.time()
}

# yfpy expects this format in token.json
with open("token.json", "w") as f:
    json.dump(manual_data, f)

print("Successfully saved token.json!")
