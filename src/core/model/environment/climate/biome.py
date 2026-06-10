from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.climate.precipitation import PrecipitationBand
from src.core.model.environment.temperature import TemperatureBand


class BiomeEnum(StrEnum):
    ICE_SHEET = "ice_sheet"
    POLAR_DESERT = "polar_desert"
    WINDFELL = "windfell"
    FROST_BOG = "frost_bog"
    ICE_MIRE = "ice_mire"
    GLACIAL_MARGIN = "glacial_margin"
    MELTING_PACK = "melting_pack"
    COLD_DESERT = "cold_desert"
    DRY_TAIGA = "dry_taiga"
    LICHEN_WOODLAND = "lichen_woodland"
    OPEN_BOREAL = "open_boreal"
    DENSE_TAIGA = "dense_taiga"
    WET_BOREAL = "wet_boreal"
    MUSKEG_BOG = "muskeg_bog"
    SAGEBRUSH_STEPPE = "sagebrush_steppe"
    SHORTGRASS_PRAIRIE = "shortgrass_prairie"
    MIXED_PRAIRIE = "mixed_prairie"
    DECIDUOUS_FOREST = "deciduous_forest"
    MOIST_TEMPERATE_FOREST = "moist_temperate_forest"
    COOL_RAINFOREST = "cool_rainforest"
    FEN_WETLAND = "fen_wetland"
    BADLANDS = "badlands"
    CHAPARRAL = "chaparral"
    WOODLAND_SAVANNA = "woodland_savanna"
    EVERGREEN_OAK_FOREST = "evergreen_oak_forest"
    LAUREL_FOREST = "laurel_forest"
    TEMPERATE_RAINFOREST = "temperate_rainforest"
    PEAT_MARSH = "peat_marsh"
    SEMI_ARID_SHRUBLAND = "semi_arid_shrubland"
    THORN_SCRUB = "thorn_scrub"
    DRY_FOREST = "dry_forest"
    MARITIME_WOODLAND = "maritime_woodland"
    SUBTROPICAL_RAINFOREST = "subtropical_rainforest"
    WARM_RAINFOREST = "warm_rainforest"
    SWAMP_FOREST = "swamp_forest"
    SAND_DESERT = "sand_desert"
    SAVANNA_SCRUB = "savanna_scrub"
    SEASONAL_FOREST = "seasonal_forest"
    MONSOON_RAINFOREST = "monsoon_rainforest"
    TROPICAL_RAINFOREST = "tropical_rainforest"
    WET_RAINFOREST = "wet_rainforest"
    MANGROVE_SWAMP = "mangrove_swamp"
    SCORCHING_WASTELAND = "scorching_wasteland"
    DRY_SAVANNA = "dry_savanna"
    MONSOON_FOREST = "monsoon_forest"
    MOIST_FOREST = "moist_forest"
    LOWLAND_RAINFOREST = "lowland_rainforest"
    EQUATORIAL_RAINFOREST = "equatorial_rainforest"
    FLOODED_JUNGLE = "flooded_jungle"


@dataclass(frozen=True)
class BiomeEnumInfo:
    label: str
    description: str
    flavor: list[str]


INFO: dict[BiomeEnum, BiomeEnumInfo] = {
    BiomeEnum.ICE_SHEET: BiomeEnumInfo(
        label="Ice sheet",
        description="Vast continental ice with little bare ground.",
        flavor=[
            "Wind scours white horizons.",
            "Crevasses hide under fresh snow.",
            "Silence swallows shouted words.",
            "The sun glares without warmth.",
            "Nothing roots here for long.",
        ],
    ),
    BiomeEnum.POLAR_DESERT: BiomeEnumInfo(
        label="Polar desert",
        description="Frozen dryness — snow is sparse and life is rarer still.",
        flavor=[
            "Gravel ridges pierce thin drifts.",
            "Ice crystals skitter over stone.",
            "Sky and ground share one pale tone.",
            "Footprints last for days.",
            "Water exists only as hard white.",
        ],
    ),
    BiomeEnum.WINDFELL: BiomeEnumInfo(
        label="Windfell",
        description="Cold, wind-scoured barrens between ice and forest.",
        flavor=[
            "Stunted growth hugs the lee of stones.",
            "Gusts erase tracks overnight.",
            "Lichens paint the rock in rust.",
            "Shelter is a depression in the earth.",
            "The horizon feels closer than it is.",
        ],
    ),
    BiomeEnum.FROST_BOG: BiomeEnumInfo(
        label="Frost bog",
        description="Frozen wetlands where thaw is brief and treacherous.",
        flavor=[
            "Moss squelches over ice.",
            "Mist rises from unexpected warmth.",
            "Boots break through crust without warning.",
            "Insects wake in sudden afternoons.",
            "Reeds rattle like dry bones.",
        ],
    ),
    BiomeEnum.ICE_MIRE: BiomeEnumInfo(
        label="Ice mire",
        description="Saturated cold ground — half water, half refusal to thaw.",
        flavor=[
            "Pools wear skins of ice by morning.",
            "Sedges stand in black water.",
            "Each step risks a cold plunge.",
            "Fog clings in the hollows.",
            "Peat smells ancient when cut.",
        ],
    ),
    BiomeEnum.GLACIAL_MARGIN: BiomeEnumInfo(
        label="Glacial margin",
        description="Where ice meets melt — unstable, loud, and raw.",
        flavor=[
            "Meltwater braids across till.",
            "Ice groans in the distance.",
            "Fresh stone shows no weathering.",
            "Cold rivers run milky with silt.",
            "Ground heaves with hidden ice.",
        ],
    ),
    BiomeEnum.MELTING_PACK: BiomeEnumInfo(
        label="Melting pack",
        description="Seasonal thaw turns snowfields into sodden tundra.",
        flavor=[
            "Slush gives way in sheets.",
            "Geese pass in ragged lines.",
            "Mud claims every low path.",
            "Nights still freeze what days undo.",
            "The land smells of wet stone.",
        ],
    ),
    BiomeEnum.COLD_DESERT: BiomeEnumInfo(
        label="Cold desert",
        description="Dry cold country — sparse plants and wide exposure.",
        flavor=[
            "Shrubs sit yards apart.",
            "Dust devils spin over gravel.",
            "Nights drop hard after pale days.",
            "Bone-white washes cut the flats.",
            "Wind finds every open seam.",
        ],
    ),
    BiomeEnum.DRY_TAIGA: BiomeEnumInfo(
        label="Dry taiga",
        description="Boreal forest on thin soil with long winters and little rain.",
        flavor=[
            "Needles carpet paths in rust.",
            "Woodpeckers echo through pines.",
            "Fires scar old trunks.",
            "Berries ripen in brief summers.",
            "Resin scents the cold air.",
        ],
    ),
    BiomeEnum.LICHEN_WOODLAND: BiomeEnumInfo(
        label="Lichen woodland",
        description="Open cold woods where lichen coats stone and bark alike.",
        flavor=[
            "Grey-green drapes every branch.",
            "Caribou moss crunches underfoot.",
            "Trees stand far enough to see between.",
            "Reindeer trails cross the moss.",
            "Light filters pale and even.",
        ],
    ),
    BiomeEnum.OPEN_BOREAL: BiomeEnumInfo(
        label="Open boreal",
        description="Northern forest with room to see the sky between spruce.",
        flavor=[
            "Needles soften footfalls.",
            "Lakes glint through the trunks.",
            "Mosquitoes own the thaw weeks.",
            "Woodsmoke drifts from distant camps.",
            "Owls call at blue dusk.",
        ],
    ),
    BiomeEnum.DENSE_TAIGA: BiomeEnumInfo(
        label="Dense taiga",
        description="Thick boreal forest — dark aisles and resinous quiet.",
        flavor=[
            "Branches snag packs and cloaks.",
            "Mushrooms crowd rotting logs.",
            "The canopy holds snow late.",
            "Paths narrow to single file.",
            "Sap runs sweet in spring wounds.",
        ],
    ),
    BiomeEnum.WET_BOREAL: BiomeEnumInfo(
        label="Wet boreal",
        description="Rain-fed northern forest with sodden ground and loud frogs.",
        flavor=[
            "Sphagnum yields like a mattress.",
            "Cranberries redden the hummocks.",
            "Black spruce lean over black water.",
            "Midges rise in clouds at dusk.",
            "Boots never fully dry here.",
        ],
    ),
    BiomeEnum.MUSKEG_BOG: BiomeEnumInfo(
        label="Muskeg bog",
        description="Acidic peatlands that swallow carelessness whole.",
        flavor=[
            "Cotton grass nods in the breeze.",
            "The ground trembles when struck.",
            "Pitcher plants wait in the sun.",
            "Old stumps stand like grave markers.",
            "Every hollow holds dark water.",
        ],
    ),
    BiomeEnum.SAGEBRUSH_STEPPE: BiomeEnumInfo(
        label="Sagebrush steppe",
        description="Cold semi-arid plains scented with sage after rain.",
        flavor=[
            "Rabbits burst from grey brush.",
            "Rain darkens the dust instantly.",
            "Ridges run on forever.",
            "Antelope paths cut straight lines.",
            "The air smells sharp and clean.",
        ],
    ),
    BiomeEnum.SHORTGRASS_PRAIRIE: BiomeEnumInfo(
        label="Shortgrass prairie",
        description="Windy grasslands cropped low by cold and graze.",
        flavor=[
            "Grass bends in rolling waves.",
            "Hawks hang on the thermals.",
            "Soil shows between turf clumps.",
            "Horizons feel honest and wide.",
            "Cattle trails harden into paths.",
        ],
    ),
    BiomeEnum.MIXED_PRAIRIE: BiomeEnumInfo(
        label="Mixed prairie",
        description="Taller grasses and forbs between dry and wet years.",
        flavor=[
            "Wildflowers punctuate the green.",
            "Pocket gophers mound the earth.",
            "Thunder builds without warning.",
            "Seed heads rattle in fall.",
            "Fire blackens strips some seasons.",
        ],
    ),
    BiomeEnum.DECIDUOUS_FOREST: BiomeEnumInfo(
        label="Deciduous forest",
        description="Hardwood country with four honest seasons.",
        flavor=[
            "Leaves gold the paths in autumn.",
            "Squirrels scold from oak limbs.",
            "Morels hide after warm rain.",
            "Sap runs in drilled maples.",
            "Understory blooms before the canopy.",
        ],
    ),
    BiomeEnum.MOIST_TEMPERATE_FOREST: BiomeEnumInfo(
        label="Moist temperate forest",
        description="Rich mid-latitude woods fed by steady rain.",
        flavor=[
            "Ferns crowd the shaded slopes.",
            "Trunks wear coats of moss.",
            "Brooks appear without maps.",
            "Deer trails lace the hollows.",
            "The air tastes green after showers.",
        ],
    ),
    BiomeEnum.COOL_RAINFOREST: BiomeEnumInfo(
        label="Cool rainforest",
        description="Wet coastal forest where drip lines never fully dry.",
        flavor=[
            "Epiphytes hang from every limb.",
            "Salmonberries ripen on the margins.",
            "Fog replaces the missing sun.",
            "Cedar scent hangs in the rain.",
            "Logs nurse whole gardens.",
        ],
    ),
    BiomeEnum.FEN_WETLAND: BiomeEnumInfo(
        label="Fen wetland",
        description="Mineral-rich wetlands alive with sedges and wading birds.",
        flavor=[
            "Reeds whisper against each other.",
            "Frogs chorus at twilight.",
            "Boots sink past the ankle.",
            "Dragonflies stitch the air.",
            "Open sky reflects in still pools.",
        ],
    ),
    BiomeEnum.BADLANDS: BiomeEnumInfo(
        label="Badlands",
        description="Eroded clay and stone — brutal heat, little mercy.",
        flavor=[
            "Gullies cut like knife work.",
            "Colors stripe the exposed walls.",
            "Shade exists only at dawn.",
            "Footing crumbles at the edge.",
            "Rain arrives as sudden violence.",
        ],
    ),
    BiomeEnum.CHAPARRAL: BiomeEnumInfo(
        label="Chaparral",
        description="Mediterranean scrub — oily plants, fire, and hard sun.",
        flavor=[
            "Sage and chamise perfume the heat.",
            "Lizards scatter on stone.",
            "Manzanita twists silver-red.",
            "Ash tells of old burns.",
            "Hills show every contour.",
        ],
    ),
    BiomeEnum.WOODLAND_SAVANNA: BiomeEnumInfo(
        label="Woodland savanna",
        description="Grasses and scattered trees in balanced open country.",
        flavor=[
            "Acorns crunch underfoot.",
            "Game paths cross the glades.",
            "Trees cast islands of shade.",
            "Fire keeps the openness honest.",
            "Birdsong carries between groves.",
        ],
    ),
    BiomeEnum.EVERGREEN_OAK_FOREST: BiomeEnumInfo(
        label="Evergreen oak forest",
        description="Live oaks and dry-adapted canopy with year-round leaf.",
        flavor=[
            "Duff muffles heavy steps.",
            "Mistletoe beads the branches.",
            "Acorn caps litter the paths.",
            "Jay cries bounce off the trunks.",
            "Sun pierces in bright coins.",
        ],
    ),
    BiomeEnum.LAUREL_FOREST: BiomeEnumInfo(
        label="Laurel forest",
        description="Lush evergreen woods of mild, humid coasts.",
        flavor=[
            "Laurel leaves shine after mist.",
            "Rills run even in dry weeks.",
            "Ivy climbs toward the light.",
            "The forest floor stays damp.",
            "Pollen hazes the spring air.",
        ],
    ),
    BiomeEnum.TEMPERATE_RAINFOREST: BiomeEnumInfo(
        label="Temperate rainforest",
        description="Enormous wet forests of mild, rainy coasts.",
        flavor=[
            "Sitka spruce tower in the drizzle.",
            "Sword ferns reach waist high.",
            "Banana slugs glisten on trails.",
            "Moss hangs in long strands.",
            "Rivers run tea-brown with tannin.",
        ],
    ),
    BiomeEnum.PEAT_MARSH: BiomeEnumInfo(
        label="Peat marsh",
        description="Slow water and deep peat — turf that remembers centuries.",
        flavor=[
            "Cotton grass sways in ranks.",
            "Cut peat stacks like dark bread.",
            "Curlews call over the flats.",
            "Boots leave lasting holes.",
            "The smell is earth and decay.",
        ],
    ),
    BiomeEnum.SEMI_ARID_SHRUBLAND: BiomeEnumInfo(
        label="Semi-arid shrubland",
        description="Dry warmth where shrubs rule and trees are guests.",
        flavor=[
            "Creosote scents the warmed air.",
            "Gravel wicks heat into evening.",
            "Jackrabbits vanish between bushes.",
            "Dry washes wait for rare floods.",
            "Thorns guard every green thing.",
        ],
    ),
    BiomeEnum.THORN_SCRUB: BiomeEnumInfo(
        label="Thorn scrub",
        description="Spiny dry brush — painful country that still blooms.",
        flavor=[
            "Mesquite claws at sleeves.",
            "Cactus flowers shock with color.",
            "Bees mob brief blossoms.",
            "Soil cracks in polygon patterns.",
            "Night cools the stones quickly.",
        ],
    ),
    BiomeEnum.DRY_FOREST: BiomeEnumInfo(
        label="Dry forest",
        description="Open woods on seasonal rain — green briefly, brown often.",
        flavor=[
            "Leaves fall with the first dry month.",
            "Wood doves coo from bare limbs.",
            "Termite mounds rise like ovens.",
            "Paths crunch with last year's leaf.",
            "Storm clouds are watched like kin.",
        ],
    ),
    BiomeEnum.MARITIME_WOODLAND: BiomeEnumInfo(
        label="Maritime woodland",
        description="Wind-shaped coastal woods salted by nearby sea air.",
        flavor=[
            "Trees lean away from the ocean.",
            "Gulls argue beyond the treeline.",
            "Salt whitens the windward bark.",
            "Fog rolls in by afternoon.",
            "Driftwood litters the streams.",
        ],
    ),
    BiomeEnum.SUBTROPICAL_RAINFOREST: BiomeEnumInfo(
        label="Subtropical rainforest",
        description="Warm, wet forest thick with palms and vines.",
        flavor=[
            "Vines bridge tree to tree.",
            "Orchids cling in the high forks.",
            "Rain hammers the broad leaves.",
            "Macaws flash through the green.",
            "Humidity beads on every surface.",
        ],
    ),
    BiomeEnum.WARM_RAINFOREST: BiomeEnumInfo(
        label="Warm rainforest",
        description="Constant warmth and rain — growth without pause.",
        flavor=[
            "Fungi sprout overnight on logs.",
            "Cicadas drown conversation.",
            "Buttress roots flare like walls.",
            "Frogs advertise from every pool.",
            "Rot and bloom trade places hourly.",
        ],
    ),
    BiomeEnum.SWAMP_FOREST: BiomeEnumInfo(
        label="Swamp forest",
        description="Flooded woods where knees and roots rise from black water.",
        flavor=[
            "Cypress knees crowd the shallows.",
            "Mosquitoes hunt in clouds.",
            "Herons stand motionless in shade.",
            "Gas bubbles burp from the muck.",
            "Boards rot between solid trunks.",
        ],
    ),
    BiomeEnum.SAND_DESERT: BiomeEnumInfo(
        label="Sand desert",
        description="Dunes and flats where water is rumor and shade is gold.",
        flavor=[
            "Sand sings under the wind.",
            "Tracks erase within an hour.",
            "Stars feel close at night.",
            "Mirages waver on the flats.",
            "Lizards leave delicate script.",
        ],
    ),
    BiomeEnum.SAVANNA_SCRUB: BiomeEnumInfo(
        label="Savanna scrub",
        description="Hot grasslands dotted with thorn trees and hard browse.",
        flavor=[
            "Acacia silhouettes the horizon.",
            "Grass fires leave black lace.",
            "Termite mounds mark old colonies.",
            "Hoofprints harden in the dust.",
            "Rain drums on broad leaves.",
        ],
    ),
    BiomeEnum.SEASONAL_FOREST: BiomeEnumInfo(
        label="Seasonal forest",
        description="Tropical woods with a dry season that strips the understory bare.",
        flavor=[
            "Leaves drop before the rains return.",
            "Monkeys riot in the canopy.",
            "Paths open when the floor clears.",
            "Epiphytes wait for the wet.",
            "Dust rises under bare feet.",
        ],
    ),
    BiomeEnum.MONSOON_RAINFOREST: BiomeEnumInfo(
        label="Monsoon rainforest",
        description="Forests ruled by dramatic wet seasons and fierce growth.",
        flavor=[
            "Rivers swell to roads overnight.",
            "Leeches wait on every leaf.",
            "Fruit falls in heavy showers.",
            "Mist lifts in steaming columns.",
            "The canopy drips long after sky clears.",
        ],
    ),
    BiomeEnum.TROPICAL_RAINFOREST: BiomeEnumInfo(
        label="Tropical rainforest",
        description="The classic equatorial forest — layered, loud, and relentless.",
        flavor=[
            "Light struggles to reach the floor.",
            "Army ants cross like a river.",
            "Toucans clack in the high green.",
            "Every niche holds a specialist.",
            "Rain arrives in warm sheets.",
        ],
    ),
    BiomeEnum.WET_RAINFOREST: BiomeEnumInfo(
        label="Wet rainforest",
        description="Perpetually soaked lowland jungle with sluggish rivers.",
        flavor=[
            "Mud sucks at every stride.",
            "Strangler figs claim old trunks.",
            "Piranha water stills between roots.",
            "Fungus glows on fallen wood.",
            "The air feels thick enough to chew.",
        ],
    ),
    BiomeEnum.MANGROVE_SWAMP: BiomeEnumInfo(
        label="Mangrove swamp",
        description="Tidal forests of salt-tolerant roots and brackish quiet.",
        flavor=[
            "Mud smells of sulfur and salt.",
            "Crabs tick across the pneumatophores.",
            "Fish snap in the root tangles.",
            "Mosquitoes own the low tide.",
            "Channels maze between the trees.",
        ],
    ),
    BiomeEnum.SCORCHING_WASTELAND: BiomeEnumInfo(
        label="Scorching wasteland",
        description="Extreme heat and drought — bare rock, salt, and survival.",
        flavor=[
            "Heat ripples above bare stone.",
            "Shade measures in inches.",
            "Salt crusts the low basins.",
            "Nothing moves at high sun.",
            "Night air still holds the burn.",
        ],
    ),
    BiomeEnum.DRY_SAVANNA: BiomeEnumInfo(
        label="Dry savanna",
        description="Hot grasslands with scattered drought-hard trees.",
        flavor=[
            "Baobabs squat on the skyline.",
            "Grass tall enough to hide a lion.",
            "Dust rises from distant herds.",
            "Fire blackens the horizon seasonally.",
            "Waterholes draw every living thing.",
        ],
    ),
    BiomeEnum.MONSOON_FOREST: BiomeEnumInfo(
        label="Monsoon forest",
        description="Woodland awakened by seasonal storms and sudden plenty.",
        flavor=[
            "New leaves flush overnight.",
            "Elephant paths trench the slopes.",
            "Streams roar then vanish.",
            "Butterflies cloud the mud puddles.",
            "Dry gullies remember water quickly.",
        ],
    ),
    BiomeEnum.MOIST_FOREST: BiomeEnumInfo(
        label="Moist forest",
        description="Warm forest with reliable rain but brief dry breathing room.",
        flavor=[
            "Palms rattle in the afternoon.",
            "Orchids colonize fallen giants.",
            "Paths slick with rotting leaf.",
            "Hornbills whoop from the canopy.",
            "Humidity lifts when the sun returns.",
        ],
    ),
    BiomeEnum.LOWLAND_RAINFOREST: BiomeEnumInfo(
        label="Lowland rainforest",
        description="Broad, hot river valleys under unbroken canopy.",
        flavor=[
            "Rivers run brown with silt.",
            "Giant lilies span the backwaters.",
            "Howler calls roll for miles.",
            "Vines as thick as a wrist.",
            "The floor steams after noon.",
        ],
    ),
    BiomeEnum.EQUATORIAL_RAINFOREST: BiomeEnumInfo(
        label="Equatorial rainforest",
        description="Year-round heat and rain — biodiversity without season.",
        flavor=[
            "No month lacks a blossom.",
            "Ant swarms cross the trails.",
            "Parrots argue in steady daylight.",
            "Rotting fruit sweetens the air.",
            "Every trunk hosts a garden.",
        ],
    ),
    BiomeEnum.FLOODED_JUNGLE: BiomeEnumInfo(
        label="Flooded jungle",
        description="Seasonally inundated forest where boats beat paths.",
        flavor=[
            "Water stands among the trunks.",
            "Fish feed in the forest shade.",
            "Lotus opens on still pools.",
            "Snakes hunt from low branches.",
            "Canoe trails mark the high water.",
        ],
    ),
}


BIOME_GRID: dict[tuple[TemperatureBand, PrecipitationBand], BiomeEnum] = {
    # ── FRIGID ────────────────────────────────────────────────────────────
    (TemperatureBand.FRIGID, PrecipitationBand.HYPER_ARID): BiomeEnum.ICE_SHEET,
    (TemperatureBand.FRIGID, PrecipitationBand.ARID): BiomeEnum.POLAR_DESERT,
    (TemperatureBand.FRIGID, PrecipitationBand.SEMI_ARID): BiomeEnum.WINDFELL,
    (TemperatureBand.FRIGID, PrecipitationBand.SUB_HUMID): BiomeEnum.FROST_BOG,
    (TemperatureBand.FRIGID, PrecipitationBand.HUMID): BiomeEnum.ICE_MIRE,
    (TemperatureBand.FRIGID, PrecipitationBand.HYPER_HUMID): BiomeEnum.GLACIAL_MARGIN,
    (TemperatureBand.FRIGID, PrecipitationBand.SATURATED): BiomeEnum.MELTING_PACK,
    # ── FREEZING ──────────────────────────────────────────────────────────
    (TemperatureBand.FREEZING, PrecipitationBand.HYPER_ARID): BiomeEnum.COLD_DESERT,
    (TemperatureBand.FREEZING, PrecipitationBand.ARID): BiomeEnum.DRY_TAIGA,
    (TemperatureBand.FREEZING, PrecipitationBand.SEMI_ARID): BiomeEnum.LICHEN_WOODLAND,
    (TemperatureBand.FREEZING, PrecipitationBand.SUB_HUMID): BiomeEnum.OPEN_BOREAL,
    (TemperatureBand.FREEZING, PrecipitationBand.HUMID): BiomeEnum.DENSE_TAIGA,
    (TemperatureBand.FREEZING, PrecipitationBand.HYPER_HUMID): BiomeEnum.WET_BOREAL,
    (TemperatureBand.FREEZING, PrecipitationBand.SATURATED): BiomeEnum.MUSKEG_BOG,
    # ── COOL ──────────────────────────────────────────────────────────────
    (TemperatureBand.COOL, PrecipitationBand.HYPER_ARID): BiomeEnum.SAGEBRUSH_STEPPE,
    (TemperatureBand.COOL, PrecipitationBand.ARID): BiomeEnum.SHORTGRASS_PRAIRIE,
    (TemperatureBand.COOL, PrecipitationBand.SEMI_ARID): BiomeEnum.MIXED_PRAIRIE,
    (TemperatureBand.COOL, PrecipitationBand.SUB_HUMID): BiomeEnum.DECIDUOUS_FOREST,
    (TemperatureBand.COOL, PrecipitationBand.HUMID): BiomeEnum.MOIST_TEMPERATE_FOREST,
    (TemperatureBand.COOL, PrecipitationBand.HYPER_HUMID): BiomeEnum.COOL_RAINFOREST,
    (TemperatureBand.COOL, PrecipitationBand.SATURATED): BiomeEnum.FEN_WETLAND,
    # ── MILD ──────────────────────────────────────────────────────────────
    (TemperatureBand.MILD, PrecipitationBand.HYPER_ARID): BiomeEnum.BADLANDS,
    (TemperatureBand.MILD, PrecipitationBand.ARID): BiomeEnum.CHAPARRAL,
    (TemperatureBand.MILD, PrecipitationBand.SEMI_ARID): BiomeEnum.WOODLAND_SAVANNA,
    (TemperatureBand.MILD, PrecipitationBand.SUB_HUMID): BiomeEnum.EVERGREEN_OAK_FOREST,
    (TemperatureBand.MILD, PrecipitationBand.HUMID): BiomeEnum.LAUREL_FOREST,
    (TemperatureBand.MILD, PrecipitationBand.HYPER_HUMID): BiomeEnum.TEMPERATE_RAINFOREST,
    (TemperatureBand.MILD, PrecipitationBand.SATURATED): BiomeEnum.PEAT_MARSH,
    # ── WARM ──────────────────────────────────────────────────────────────
    (TemperatureBand.WARM, PrecipitationBand.HYPER_ARID): BiomeEnum.SEMI_ARID_SHRUBLAND,
    (TemperatureBand.WARM, PrecipitationBand.ARID): BiomeEnum.THORN_SCRUB,
    (TemperatureBand.WARM, PrecipitationBand.SEMI_ARID): BiomeEnum.DRY_FOREST,
    (TemperatureBand.WARM, PrecipitationBand.SUB_HUMID): BiomeEnum.MARITIME_WOODLAND,
    (TemperatureBand.WARM, PrecipitationBand.HUMID): BiomeEnum.SUBTROPICAL_RAINFOREST,
    (TemperatureBand.WARM, PrecipitationBand.HYPER_HUMID): BiomeEnum.WARM_RAINFOREST,
    (TemperatureBand.WARM, PrecipitationBand.SATURATED): BiomeEnum.SWAMP_FOREST,
    # ── HOT ───────────────────────────────────────────────────────────────
    (TemperatureBand.HOT, PrecipitationBand.HYPER_ARID): BiomeEnum.SAND_DESERT,
    (TemperatureBand.HOT, PrecipitationBand.ARID): BiomeEnum.SAVANNA_SCRUB,
    (TemperatureBand.HOT, PrecipitationBand.SEMI_ARID): BiomeEnum.SEASONAL_FOREST,
    (TemperatureBand.HOT, PrecipitationBand.SUB_HUMID): BiomeEnum.MONSOON_RAINFOREST,
    (TemperatureBand.HOT, PrecipitationBand.HUMID): BiomeEnum.TROPICAL_RAINFOREST,
    (TemperatureBand.HOT, PrecipitationBand.HYPER_HUMID): BiomeEnum.WET_RAINFOREST,
    (TemperatureBand.HOT, PrecipitationBand.SATURATED): BiomeEnum.MANGROVE_SWAMP,
    # ── SCORCHING ───────────────────────────────────────────────────────
    (TemperatureBand.SCORCHING, PrecipitationBand.HYPER_ARID): BiomeEnum.SCORCHING_WASTELAND,
    (TemperatureBand.SCORCHING, PrecipitationBand.ARID): BiomeEnum.DRY_SAVANNA,
    (TemperatureBand.SCORCHING, PrecipitationBand.SEMI_ARID): BiomeEnum.MONSOON_FOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.SUB_HUMID): BiomeEnum.MOIST_FOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.HUMID): BiomeEnum.LOWLAND_RAINFOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.HYPER_HUMID): BiomeEnum.EQUATORIAL_RAINFOREST,
    (TemperatureBand.SCORCHING, PrecipitationBand.SATURATED): BiomeEnum.FLOODED_JUNGLE,
}
