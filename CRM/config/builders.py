# ── Existing Builders ─────────────────────────────────────────────
from src.builders.sis_builder import SISBuilder
from src.builders.sp_builder import SPBuilder
from src.builders.kg_builder import KGBuilder
from src.builders.radiance_builder import RadianceBuilder
from src.builders.sameera_builder import SameeraBuilder
from src.builders.royal_builder import RoyalBuilder
from src.builders.lml_builder import LMLBuilder
from src.builders.selldo_api_builder import SellDoAPIBuilder
from src.builders.salesrobot_builder import SalesRobotBuilder
from src.builders.stepsstone_selldo_builder import StepsStoneSellDoBuilder
from src.builders.bbcl_builder import BBCLBuilder
from src.builders.dac_builder import DACBuilder
from src.builders.vgk_builder import VGKBuilder
from src.builders.isha_builder import IshaBuilder
from src.builders.urbanise_builder import UrbaniseBuilder
from src.builders.elephantine_builder import ElephantineBuilder
from src.builders.adityaram_builder import AdityaramBuilder
from src.builders.vgn360_builder import VGN360Builder
from src.builders.marutham_builder import MaruthamBuilder

# ── New Builders (Rails/Sell.do CSRF + fetch) ─────────────────────
from src.builders.gt_bharathi_builder import GTBharathiBuilder
from src.builders.mp_builder import MPBuilder
from src.builders.altis_builder import AltisBuilder
from src.builders.lancor_builder import LancorBuilder
from src.builders.es_builder import ESBuilder
from src.builders.vr_builder import VRBuilder
from src.builders.taj_builder import TajBuilder
from src.builders.voora_builder import VooraBuilder
from src.builders.navins_builder import NavinsBuilder
from src.builders.nutech_builder import NutechBuilder

# ── New Builders (ASP.NET WebForms — Playwright UI) ───────────────
from src.builders.vnr_builder import VNRBuilder
from src.builders.sip_builder import SIPBuilder

# ── New Builders (Salesforce / Firebase — Playwright UI) ──────────
from src.builders.tvs_builder import TVSBuilder
from src.builders.sobha_builder import SobhaBuilder
from src.builders.siddarth_builder import SiddarthBuilder
from src.builders.urbantree_builder import UrbantreeBuilder
from src.builders.praganya_builder import PraganyaBuilder
from src.builders.vista_builder import VistaBuilder
from src.builders.dra_builder import DRABuilder


# Registry for dynamic class lookup from DB crm_type
# Maps the 'crm_type' column in the 'builders' table to the corresponding Python class.
BUILDER_CLASS_MAP = {
    # ── StepsStone / SellDo family ─────────────────────────────────
    "sis":               SISBuilder,
    "sp":                SPBuilder,
    "kg":                KGBuilder,
    "radiance":          RadianceBuilder,
    "sameera":           SameeraBuilder,
    "royal":             RoyalBuilder,
    "lml":               LMLBuilder,
    "selldo":            SellDoAPIBuilder,
    "stepsstone_selldo": StepsStoneSellDoBuilder,

    # ── SalesRobot ─────────────────────────────────────────────────
    "salesrobot":        SalesRobotBuilder,
    "urbantree":         UrbantreeBuilder,
    "praganya":          PraganyaBuilder,
    "dra":               DRABuilder,
    "iris":              DRABuilder,

    # ── Realty World / Listez ─────────────────────────────────────
    "vista":             VistaBuilder,
    "rwd":               VistaBuilder,

    # ── API-based ──────────────────────────────────────────────────
    "bbcl":              BBCLBuilder,

    # ── Playwright UI — previously integrated ─────────────────────
    "dac":               DACBuilder,
    "vgk":               VGKBuilder,
    "isha":              IshaBuilder,
    "urbanise":          UrbaniseBuilder,
    "elephantine":       ElephantineBuilder,
    "adityaram":         AdityaramBuilder,
    "vgn360":            VGN360Builder,

    # ── Rails/Sell.do CSRF + fetch — newly integrated ─────────────
    "gt_bharathi":       GTBharathiBuilder,
    "mp":                MPBuilder,
    "altis":             AltisBuilder,
    "lancor":            LancorBuilder,
    "es":                ESBuilder,
    "vr":                VRBuilder,
    "taj":               TajBuilder,
    "voora":             VooraBuilder,
    "navins":            NavinsBuilder,
    "nutech":            NutechBuilder,

    # ── ASP.NET WebForms — newly integrated ───────────────────────
    "vnr":               VNRBuilder,
    "sip":               SIPBuilder,

    # ── Salesforce / Firebase — newly integrated ──────────────────
    "tvs":               TVSBuilder,
    "sobha":             SobhaBuilder,
    "siddarth":          SiddarthBuilder,
}
