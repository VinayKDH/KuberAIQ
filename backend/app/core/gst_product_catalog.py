"""GST HSN/SAC product catalogue — keyword → code/rate for MSME invoicing."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GstProductCatalogEntry:
    """One catalogue row: canonical label, HSN/SAC, GST %, search keywords."""

    label: str
    hsn_sac: str
    gst_rate: str
    keywords: tuple[str, ...]


# Curated MSME catalogue (HSN chapter codes + common SAC services).
# Keywords are lowercase; matching uses word boundaries and substring scoring.
GST_PRODUCT_CATALOG: tuple[GstProductCatalogEntry, ...] = (
    # --- Dairy & staples (0–5%) ------------------------------------------------
    GstProductCatalogEntry("Fresh milk", "0401", "0", ("milk", "doodh", "fresh milk", "toned milk")),
    GstProductCatalogEntry("Milk powder / khoya", "0402", "5", ("khoya", "mawa", "milk powder", "dairy whitener", "skimmed milk")),
    GstProductCatalogEntry("Curd / yoghurt", "0403", "5", ("curd", "dahi", "yoghurt", "yogurt", "lassi", "buttermilk")),
    GstProductCatalogEntry("Butter / ghee", "0405", "12", ("butter", "ghee", "makhan", "clarified butter")),
    GstProductCatalogEntry("Paneer / cheese", "0406", "5", ("paneer", "cheese", "cottage cheese", "processed cheese")),
    GstProductCatalogEntry("Eggs", "0407", "0", ("egg", "eggs", "anda")),
    GstProductCatalogEntry("Honey", "0409", "5", ("honey", "shahad")),
    GstProductCatalogEntry("Fresh vegetables", "0701", "0", ("vegetable", "vegetables", "sabzi", "onion", "potato", "tomato")),
    GstProductCatalogEntry("Fresh fruits", "0803", "0", ("fruit", "fruits", "apple", "banana", "mango", "orange")),
    GstProductCatalogEntry("Pulses / dal", "0713", "0", ("dal", "pulses", "chana", "moong", "urad", "toor", "masoor", "rajma")),
    GstProductCatalogEntry("Wheat / atta", "1001", "0", ("wheat", "atta", "flour", "maida", "besan", "sooji", "rava")),
    GstProductCatalogEntry("Rice", "1006", "0", ("rice", "chawal", "basmati", "poha", "rice flour")),
    GstProductCatalogEntry("Sugar", "1701", "5", ("sugar", "chini", "jaggery", "gur")),
    GstProductCatalogEntry("Salt", "2501", "0", ("salt", "namak", "iodized salt")),
    GstProductCatalogEntry("Tea", "0902", "5", ("tea", "chai", "tea leaves", "green tea")),
    GstProductCatalogEntry("Coffee", "0901", "5", ("coffee", "coffee powder", "instant coffee")),
    GstProductCatalogEntry("Spices", "0910", "5", ("spice", "spices", "masala", "turmeric", "haldi", "chilli", "cumin", "jeera", "coriander", "pepper")),
    GstProductCatalogEntry("Edible oil", "1507", "5", ("edible oil", "cooking oil", "mustard oil", "sunflower oil", "soyabean oil", "groundnut oil")),
    GstProductCatalogEntry("Bread / bakery", "1905", "5", ("bread", "pav", "bun", "bakery", "cake", "pastry")),
    GstProductCatalogEntry("Biscuits / snacks", "1905", "18", ("biscuit", "cookie", "namkeen", "snack", "chips", "kurkure", "wafers")),
    GstProductCatalogEntry("Noodles / pasta", "1902", "18", ("noodle", "noodles", "maggi", "pasta", "macaroni")),
    GstProductCatalogEntry("Pickles / sauces", "2103", "12", ("pickle", "achar", "sauce", "ketchup", "chutney")),
    GstProductCatalogEntry("Soft drinks", "2202", "28", ("soft drink", "cola", "soda", "cold drink", "pepsi", "coke")),
    GstProductCatalogEntry("Mineral water", "2201", "18", ("mineral water", "bottled water", "packaged water")),
    GstProductCatalogEntry("Ice cream", "2105", "18", ("ice cream", "icecream", "kulfi")),
    GstProductCatalogEntry("Frozen meat / fish", "0207", "0", ("chicken", "mutton", "fish", "meat", "poultry", "seafood")),
    # --- Construction & building materials ---------------------------------------
    GstProductCatalogEntry("Cement", "2523", "28", ("cement", "opc", "ppc", "portland cement", "grade cement", "white cement")),
    GstProductCatalogEntry("Ready-mix concrete", "3824", "28", ("rmc", "ready mix", "readymix concrete", "concrete mix")),
    GstProductCatalogEntry("Ceramic tiles", "6907", "28", ("tile", "tiles", "ceramic tile", "vitrified", "floor tile", "wall tile")),
    GstProductCatalogEntry("Marble / granite", "6802", "28", ("marble", "granite", "kotah stone", "stone slab")),
    GstProductCatalogEntry("Steel / TMT bars", "7214", "18", ("steel", "tmt", "tmt bar", "rebar", "rod", "ms rod", "sariya", "iron bar")),
    GstProductCatalogEntry("Structural steel", "7216", "18", ("structural steel", "i beam", "h beam", "angle", "channel", "ms angle")),
    GstProductCatalogEntry("Binding wire", "7217", "18", ("binding wire", "gi wire", "ms wire")),
    GstProductCatalogEntry("Paint", "3209", "28", ("paint", "emulsion", "enamel paint", "primer", "distemper", "putty")),
    GstProductCatalogEntry("Sand / aggregate", "2517", "5", ("sand", "aggregate", "gravel", "gitti", "crushed stone", "stone dust")),
    GstProductCatalogEntry("Bricks", "6901", "12", ("brick", "bricks", "aac block", "fly ash brick", "clay brick")),
    GstProductCatalogEntry("Plywood / timber", "4412", "18", ("plywood", "timber", "wood board", "laminate", "mdf", "particle board")),
    GstProductCatalogEntry("Glass", "7005", "18", ("glass", "float glass", "toughened glass", "window glass")),
    GstProductCatalogEntry("Aluminium sections", "7604", "18", ("aluminium section", "aluminium profile", "aluminium window", "aluminium door")),
    GstProductCatalogEntry("Waterproofing compound", "3214", "18", ("waterproofing", "water proofing", "dr fixit", "sealant")),
    GstProductCatalogEntry("Adhesive / Fevicol", "3506", "18", ("adhesive", "fevicol", "glue", "epoxy", "araldite")),
    GstProductCatalogEntry("Nails / screws / fasteners", "7318", "18", ("nail", "nails", "screw", "screws", "fastener", "bolt", "nut", "washer")),
    GstProductCatalogEntry("Door / window fittings", "8302", "18", ("hinge", "door handle", "door lock", "tower bolt", "door closer")),
    GstProductCatalogEntry("Roofing sheets", "7210", "18", ("roofing sheet", "gi sheet", "color coated sheet", "polycarbonate sheet")),
    # --- Plumbing & sanitary -----------------------------------------------------
    GstProductCatalogEntry("PVC pipes", "3917", "18", ("pvc pipe", "upvc", "cpvc", "pipe", "plumbing pipe")),
    GstProductCatalogEntry("Pipe fittings", "3917", "18", ("elbow", "tee", "coupler", "pipe fitting", "pvc fitting")),
    GstProductCatalogEntry("Sanitaryware", "6910", "18", ("sanitaryware", "toilet", "commode", "wash basin", "basin", "urinal")),
    GstProductCatalogEntry("Taps / faucets", "8481", "18", ("tap", "faucet", "mixer tap", "bathroom tap", "pillar tap")),
    GstProductCatalogEntry("Shower / bathroom accessories", "3922", "18", ("shower", "health faucet", "bathroom accessory", "towel rod")),
    GstProductCatalogEntry("Water pump / motor", "8413", "18", ("water pump", "submersible pump", "motor pump", "monoblock pump")),
    GstProductCatalogEntry("Water tank", "3925", "18", ("water tank", "loft tank", "sintex tank", "storage tank")),
    GstProductCatalogEntry("Geyser / water heater", "8516", "18", ("geyser", "water heater", "immersion rod")),
    # --- Electrical ----------------------------------------------------------------
    GstProductCatalogEntry("Electrical wire / cable", "8544", "18", ("wire", "cable", "electrical wire", "copper wire", "house wire", "armoured cable")),
    GstProductCatalogEntry("Switch / MCB / DB", "8536", "18", ("switch", "mcb", "socket", "electrical switch", "distribution board", "db box", "mcb box")),
    GstProductCatalogEntry("LED bulb / tube light", "8539", "18", ("led bulb", "tube light", "led tube", "bulb", "cfl", "lighting")),
    GstProductCatalogEntry("Ceiling fan", "8414", "18", ("fan", "ceiling fan", "exhaust fan", "table fan")),
    GstProductCatalogEntry("Inverter / UPS", "8504", "18", ("inverter", "ups", "power inverter")),
    GstProductCatalogEntry("Battery", "8507", "18", ("battery", "inverter battery", "tubular battery", "car battery")),
    GstProductCatalogEntry("Conduit / junction box", "3917", "18", ("conduit", "junction box", "pvc conduit", "casing capping")),
    GstProductCatalogEntry("Stabilizer", "9032", "18", ("stabilizer", "voltage stabilizer")),
    # --- Electronics & appliances --------------------------------------------------
    GstProductCatalogEntry("Computers", "8471", "18", ("computer", "laptop", "desktop", "pc", "notebook", "all in one")),
    GstProductCatalogEntry("Mobile phones", "8517", "18", ("mobile", "phone", "smartphone", "cellphone", "iphone", "android phone")),
    GstProductCatalogEntry("Tablet", "8471", "18", ("tablet", "ipad", "android tablet")),
    GstProductCatalogEntry("Printer / scanner", "8443", "18", ("printer", "scanner", "multifunction printer", "photocopier")),
    GstProductCatalogEntry("TV / monitor", "8528", "18", ("television", "tv", "led tv", "monitor", "display")),
    GstProductCatalogEntry("Refrigerator", "8418", "18", ("refrigerator", "fridge", "deep freezer")),
    GstProductCatalogEntry("Washing machine", "8450", "18", ("washing machine", "washer", "semi automatic washing machine")),
    GstProductCatalogEntry("Air conditioner", "8415", "18", ("air conditioner", "ac", "split ac", "window ac")),
    GstProductCatalogEntry("Microwave / OTG", "8516", "18", ("microwave", "otg", "oven", "microwave oven")),
    GstProductCatalogEntry("Router / networking", "8517", "18", ("router", "wifi router", "modem", "network switch", "lan cable")),
    # --- Hardware & tools ----------------------------------------------------------
    GstProductCatalogEntry("Hand tools", "8205", "18", ("hammer", "spanner", "wrench", "plier", "pliers", "screwdriver", "chisel")),
    GstProductCatalogEntry("Power tools", "8467", "18", ("drill machine", "angle grinder", "cutting machine", "power tool", "impact drill")),
    GstProductCatalogEntry("Welding rods / equipment", "8311", "18", ("welding rod", "electrode", "welding machine", "welder")),
    GstProductCatalogEntry("Measuring tape / level", "9015", "18", ("measuring tape", "spirit level", "measuring instrument")),
    GstProductCatalogEntry("Safety equipment", "6506", "18", ("helmet", "safety shoe", "gloves", "safety jacket", "goggle")),
    # --- Automotive ----------------------------------------------------------------
    GstProductCatalogEntry("Tyres", "4011", "28", ("tyre", "tyres", "tire", "car tyre", "bike tyre")),
    GstProductCatalogEntry("Tubes", "4013", "28", ("tube", "tyre tube", "inner tube")),
    GstProductCatalogEntry("Engine oil / lubricant", "2710", "18", ("engine oil", "lubricant", "lube oil", "gear oil", "hydraulic oil")),
    GstProductCatalogEntry("Diesel", "2710", "18", ("diesel", "gas oil", "high speed diesel")),
    GstProductCatalogEntry("Petrol", "2710", "18", ("petrol", "gasoline", "motor spirit", "ms petrol")),
    GstProductCatalogEntry("Auto spare parts", "8708", "28", ("spare part", "auto part", "brake pad", "clutch plate", "filter", "air filter", "oil filter")),
    # --- Textiles & garments ---------------------------------------------------------
    GstProductCatalogEntry("Cotton fabric", "5208", "5", ("cotton", "cotton fabric", "cloth", "textile fabric")),
    GstProductCatalogEntry("Synthetic fabric", "5407", "12", ("polyester fabric", "synthetic fabric", "nylon fabric")),
    GstProductCatalogEntry("Readymade garments", "6109", "5", ("garment", "shirt", "tshirt", "t-shirt", "apparel", "clothing", "trouser", "jeans")),
    GstProductCatalogEntry("Saree / ethnic wear", "6204", "5", ("saree", "sari", "kurta", "salwar", "ethnic wear", "lehenga")),
    GstProductCatalogEntry("Towel / bedsheet", "6302", "5", ("towel", "bedsheet", "bed sheet", "blanket", "quilt", "pillow cover")),
    GstProductCatalogEntry("Footwear", "6403", "5", ("footwear", "shoe", "shoes", "sandal", "slipper", "chappal")),
    # --- Pharma & personal care ----------------------------------------------------
    GstProductCatalogEntry("Medicines", "3004", "12", ("medicine", "tablet", "pharma", "drug", "syrup", "capsule", "injection", "ointment")),
    GstProductCatalogEntry("Ayurvedic products", "3004", "12", ("ayurvedic", "herbal medicine", "churna", "ayurveda")),
    GstProductCatalogEntry("Soap / detergent", "3401", "18", ("soap", "detergent", "washing powder", "liquid detergent", "surf")),
    GstProductCatalogEntry("Shampoo / cosmetics", "3305", "18", ("shampoo", "conditioner", "cosmetic", "cream", "lotion", "face wash")),
    GstProductCatalogEntry("Sanitizer / disinfectant", "3808", "18", ("sanitizer", "hand sanitizer", "disinfectant", "phenyl", "floor cleaner")),
    GstProductCatalogEntry("Diapers / sanitary napkins", "9619", "12", ("diaper", "sanitary napkin", "pad", "baby diaper")),
    # --- Plastic & packaging -------------------------------------------------------
    GstProductCatalogEntry("Plastic goods", "3923", "18", ("plastic", "plastic container", "bucket", "mug", "plastic chair")),
    GstProductCatalogEntry("Corrugated boxes", "4819", "12", ("corrugated box", "carton", "packaging box", "cardboard box")),
    GstProductCatalogEntry("Packaging tape", "3919", "18", ("packaging tape", "brown tape", "cello tape", "stretch film", "shrink wrap")),
    # --- Furniture & office --------------------------------------------------------
    GstProductCatalogEntry("Office furniture", "9403", "18", ("office chair", "office table", "workstation", "desk", "cabinet", "furniture")),
    GstProductCatalogEntry("Home furniture", "9403", "18", ("sofa", "bed", "mattress", "wardrobe", "dining table", "chair")),
    GstProductCatalogEntry("Stationery", "4820", "12", ("stationery", "notebook", "register", "paper", "a4 paper", "copier paper")),
    GstProductCatalogEntry("Pen / pencil", "9608", "12", ("pen", "pencil", "marker", "highlighter")),
    GstProductCatalogEntry("Printer cartridge / toner", "8443", "18", ("cartridge", "toner", "ink cartridge", "printer cartridge")),
    # --- Agriculture & irrigation --------------------------------------------------
    GstProductCatalogEntry("Fertilizer", "3102", "5", ("fertilizer", "fertiliser", "urea", "dap", "npk")),
    GstProductCatalogEntry("Pesticide / insecticide", "3808", "18", ("pesticide", "insecticide", "herbicide", "fungicide")),
    GstProductCatalogEntry("Seeds", "1209", "0", ("seed", "seeds", "hybrid seed", "vegetable seed")),
    GstProductCatalogEntry("Drip irrigation", "8424", "12", ("drip irrigation", "sprinkler", "irrigation pipe", "drip line")),
    GstProductCatalogEntry("Tractor spare parts", "8708", "18", ("tractor part", "tractor spare", "pTO shaft")),
    # --- Metals & industrial raw materials -----------------------------------------
    GstProductCatalogEntry("Copper / brass", "7408", "18", ("copper", "brass", "copper wire scrap", "brass fitting")),
    GstProductCatalogEntry("Aluminium sheets", "7606", "18", ("aluminium sheet", "aluminium coil", "aluminium plate")),
    GstProductCatalogEntry("Stainless steel", "7219", "18", ("stainless steel", "ss sheet", "ss pipe", "ss rod")),
    GstProductCatalogEntry("Rubber products", "4016", "18", ("rubber", "rubber sheet", "hose pipe", "rubber gasket")),
    # --- SAC — services ------------------------------------------------------------
    GstProductCatalogEntry("Restaurant services", "9963", "18", ("restaurant", "catering", "food service", "dining", "tiffin service")),
    GstProductCatalogEntry("Hotel accommodation", "9963", "18", ("hotel", "lodging", "accommodation", "room rent", "guest house")),
    GstProductCatalogEntry("Professional services", "9983", "18", ("consulting", "consultancy", "professional service", "advisory", "legal service", "ca service", "audit fee")),
    GstProductCatalogEntry("IT / software services", "9983", "18", ("software service", "it service", "saas", "web development", "app development", "hosting")),
    GstProductCatalogEntry("Advertising / marketing", "9983", "18", ("advertising", "marketing", "digital marketing", "seo", "branding")),
    GstProductCatalogEntry("Maintenance services", "9987", "18", ("maintenance", "repair service", "amc", "annual maintenance", "facility management")),
    GstProductCatalogEntry("Freight / transport", "9965", "18", ("freight", "transport", "logistics", "courier", "cargo", "shipping", "goods transport")),
    GstProductCatalogEntry("Renting of machinery", "9973", "18", ("equipment rental", "machinery hire", "crane hire", "jcb rental")),
    GstProductCatalogEntry("Beauty / salon services", "9997", "18", ("salon", "beauty parlour", "spa", "haircut", "grooming")),
    GstProductCatalogEntry("Gym / fitness services", "9997", "18", ("gym", "fitness", "yoga class", "personal training")),
    GstProductCatalogEntry("Insurance brokerage", "9971", "18", ("insurance", "insurance premium", "brokerage")),
    GstProductCatalogEntry("Training / coaching", "9992", "18", ("training", "coaching", "tuition", "course fee", "workshop")),
    GstProductCatalogEntry("Printing services", "9989", "18", ("printing service", "flex printing", "banner printing", "visiting card printing")),
)
