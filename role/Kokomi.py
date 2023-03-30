from ..classmodel import Buff, BuffInfo, Dmg, DmgBonus, FixValue, Multiplier
from ..dmg_calc import DmgCalc
from ._model import Role


class Kokomi(Role):
    name = "心海"

    # TODO:只额外增伤生命值倍率部分， 用exclude_buff
    def buff_T2(self, buff_info: BuffInfo, prop: DmgCalc):
        """真珠御呗"""
        dmg_bonus = prop.healing * 0.15
        buff_info.buff = Buff(
            dsc=f"仪来羽衣状态下，普攻和重击基于治疗加成的15%获得额外增伤+{dmg_bonus*100}%",
            dmg_bonus=dmg_bonus,
        )

    C2_healing_bonus_E: float = 0
    """波起云海对化海月提升"""
    C2_healing_bonus_A: float = 0
    """波起云海对普攻和重击提升"""

    def buff_C2(self, buff_info: BuffInfo):
        """波起云海"""
        buff_info.buff = Buff(
            dsc="对生命值低于50%的角色，回复倍率化海月+4.5%生命值上限，普攻和重击+0.6%生命值上限",
        )
        self.C2_healing_bonus_E = 4.5
        self.C2_healing_bonus_A = 0.6

    def buff_C6(self, buff_info: BuffInfo):
        """珊瑚一心"""
        buff_info.buff = Buff(
            dsc="仪来羽衣状态下，普攻和重击为生命值高于80%的角色恢复4秒内，水伤+40%",
            elem_dmg_bonus=DmgBonus(hydro=0.4),
        )

    def skill_E(self, dmg_info: Dmg):
        """海月之誓"""
        calc = self.create_calc()
        scaler, fix_value = [
            float(num)
            for num in self.get_scaler("海月之誓", self.talents[1].level, "治疗量")
            .replace("%生命值上限", "")
            .split("+")
        ]
        calc.set(
            multiplier=Multiplier(atk=scaler),
            fix_value=FixValue(heal=fix_value),
            exlude_buffs=dmg_info.exclude_buff,
        )
        dmg_info.exp_value = int(calc.calc_dmg.get_healing())

    def buff_Q(self, buff_info: BuffInfo):
        """海人化羽·仪来羽衣"""
        multip = float(
            self.get_scaler("海人化羽", self.talents[2].level, "普通攻击伤害提升").replace(
                "%生命值上限", ""
            )
        )
        buff_info.buff = Buff(
            dsc=f"仪来羽衣状态下，普攻倍率+{multip}%生命值上限",
            multiplier=Multiplier(hp=multip),
        )

    @property
    def valid_prop(self) -> list[str]:
        """有效属性"""
        return []

    def setting(self, labels: dict = {}) -> list[BuffInfo]:
        """增益设置"""
        output: list[BuffInfo] = []
        # 天赋
        if self.info.ascension >= 4:
            output.append(
                BuffInfo(
                    source=f"{self.name}-T2",
                    name="真珠御呗",
                )
            )
        # 命座
        if self.info.constellation >= 2:
            output.append(
                BuffInfo(
                    source=f"{self.name}-C2",
                    name="波起云海",
                )
            )
            if self.info.constellation >= 4:
                output.append(
                    BuffInfo(
                        source=f"{self.name}-C6",
                        name="珊瑚一心",
                        buff_type="propbuff",
                    )
                )
        # 技能
        output.append(
            BuffInfo(
                source=f"{self.name}-Q",
                name="海人化羽",
            )
        )
        return output

    def buff(self, buff_list: list[BuffInfo], prop):
        """增益列表"""
        for buff in buff_list:
            match buff.name:
                case "真珠御呗":
                    self.buff_T2(buff, prop)
                case "波起云海":
                    self.buff_C2(buff)
                case "珊瑚一心":
                    self.buff_C6(buff)
                case "海人化羽":
                    self.buff_Q(buff)

    def weight(self, weights: dict, ex_buffs: dict):
        """伤害权重"""
        self.dmg_list = [
            Dmg(
                index=0,
                name="充能效率阈值",
                weight=weights.get("充能效率阈值", 100),
            ),
            Dmg(
                index=1,
                source="E",
                name="海月之誓",
                value_type="H",
                dsc="E每跳治疗",
                weight=weights.get("海月之誓", 0),
                exclude_buff=ex_buffs.get("海月之誓", []),
            ),
        ]

    def dmg(self) -> list[Dmg]:
        """伤害列表"""
        for dmg in self.dmg_list:
            if dmg.weight != 0:
                match dmg.name:
                    case "海月之誓":
                        self.skill_E(dmg)
        return self.dmg_list

    def weights_init(self, style_name: str = "") -> dict[str, int]:
        """角色出伤流派"""
        match style_name:
            case _:
                return {
                    "充能效率阈值": 160,
                    "海月之誓": 10,
                }
