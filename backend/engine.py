"""与 Renhuai123/ziwei-doushu 起盘引擎对齐的展示适配层。
完整引擎在上游 lib/ziwei/；v4 数据已按该引擎预先生成，本服务不实时计算。
"""
PALACES = ["命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫", "迁移宫", "交友宫", "官禄宫", "田宅宫", "福德宫", "父母宫"]

def build_palaces(first_star):
    # v4 每行只保存命宫第一主星；空值是合法的“命无正曜”。
    return [{"name": name, "stars": ([first_star] if i == 0 and first_star else [])} for i, name in enumerate(PALACES)]
