"""
Prompt Library — 200+ prompts across 15 categories for clip art generation
These are seed prompts. Groq expands them into specific image prompts.
"""

CATEGORIES = {
    "boho_florals": {
        "name": "Boho Florals",
        "niche": "Wedding invites, journals, wall art",
        "pricing_tier": "mega_pack",
        "prompts": [
            "boho wildflower bouquet", "pampas grass arrangement", "dried flower wreath",
            "boho rose illustration", "eucalyptus branch watercolor", "terracotta floral bunch",
            "boho sunflower sketch", "lavender bundle minimalist", "wildflower meadow border",
            "boho tulip line art", "dried palm leaf", "rattan flower basket",
            "boho peony drawing", "sage green botanical", "rustic daisy chain",
            "boho lily illustration", "chamomile cluster", "poppy field sketch",
            "boho hydrangea", "botanical frame boho", "boho fern leaves",
            "wild rose vine", "boho carnation bunch", "thistle boho style",
            "boho ranunculus", "anemone flower boho", "boho carnation wreath",
            "wildflower bouquet minimalist", "boho garden rose", "dried baby breath",
            "boho iris drawing", "cosmos flower boho", "boho marigold",
            "wildflower garland", "boho chrysanthemum", "aster flower boho",
            "boho dahlia sketch", "foxglove boho style", "boho snapdragon",
            "hollyhock boho illustration", "boho sweet pea", "lisianthus boho",
            "boho freesia", "zinnia boho bundle", "boho morning glory",
            "boho hibiscus", "plumeria boho style", "boho bird of paradise",
            "boho orchid sketch", "stephanotis boho", "boho gardenia"
        ]
    },
    "kawaii_cute": {
        "name": "Kawaii & Cute",
        "niche": "Planner stickers, nursery art, kids products",
        "pricing_tier": "starter_pack",
        "prompts": [
            "kawaii cat face", "cute bunny illustration", "kawaii cloud smile",
            "cute bear character", "kawaii star face", "cute rainbow drawing",
            "kawaii food set", "cute planet illustration", "kawaii ghost cute",
            "cute mushroom character", "kawaii avocado", "cute dinosaur cartoon",
            "kawaii sushi set", "cute cactus face", "kawaii pineapple happy",
            "cute cupcake character", "kawaii ice cream cone", "cute donut illustration",
            "kawaii coffee cup", "cute toast character", "kawaii egg illustration",
            "cute banana face", "kawaii strawberry happy", "cute watermelon slice",
            "kawaii peach character", "kawaii lemon face", "cute apple cartoon",
            "kawaii cherry pair", "cute grape bunch happy", "kawaii orange slice",
            "kawaii panda face", "cute koala character", "kawaii penguin happy",
            "cute fox face", "kawaii owl character", "cute hedgehog smile",
            "kawaii frog face", "cute ladybug cartoon", "kawaii bee character",
            "cute butterfly smile", "kawaii snail character", "cute turtle face",
            "kawaii whale illustration", "cute dolphin cartoon", "kawaii octopus face",
            "cute shark smile", "kawaii fish character", "cute jellyfish happy",
            "kawaii seashell character", "cute starfish smile"
        ]
    },
    "vintage_retro": {
        "name": "Vintage & Retro",
        "niche": "Retro branding, poster design, merch",
        "pricing_tier": "mega_pack",
        "prompts": [
            "retro sunset gradient", "vintage badge emblem", "retro typography banner",
            "vintage coffee label", "retro gas station sign", "vintage camera illustration",
            "retro car sketch", "vintage microphone", "retro radio illustration",
            "vintage compass drawing", "retro rocket ship", "vintage typewriter",
            "retro neon sign", "vintage record player", "retro pin-up style",
            "vintage postcard frame", "retro TV illustration", "vintage telephone",
            "retro bowling pin", "vintage jukebox", "retro roller skate",
            "vintage surfboard", "retro cassette tape", "vintage floppy disk",
            "retro arcade machine", "vintage polaroid camera", "retro boombox",
            "vintage sewing machine", "retro alarm clock", "vintage desk lamp",
            "retro luggage set", "vintage globe illustration", "retro binoculars",
            "vintage trophy", "retro wrench tool", "vintage pocket watch",
            "retro top hat", "vintage cane walking stick", "retro monocle",
            "vintage key ornate", "retro mirror ornate", "vintage picture frame",
            "retro candlestick", "vintage tea kettle", "retro toaster",
            "vintage mixer kitchen", "retro iron clothes", "vintage vacuum cleaner",
            "retro blender kitchen", "vintage fan table"
        ]
    },
    "watercolor_elements": {
        "name": "Watercolor Elements",
        "niche": "Wedding, greeting cards, journals",
        "pricing_tier": "mega_pack",
        "prompts": [
            "watercolor splash abstract", "watercolor floral bouquet", "watercolor galaxy",
            "watercolor mountain landscape", "watercolor ocean waves", "watercolor sunset",
            "watercolor feather", "watercolor butterfly", "watercolor peacock feather",
            "watercolor lemon", "watercolor orange slice", "watercolor strawberry",
            "watercolor cherry pair", "watercolor grape cluster", "watercolor apple",
            "watercolor pear", "watercolor peach", "watercolor watermelon",
            "watercolor pineapple", "watercolor coconut", "watercolor kiwi slice",
            "watercolor mango", "watercolor pomegranate", "watercolor fig",
            "watercolor plum", "watercolor apricot", "watercolor nectarine",
            "watercolor raspberry", "watercolor blackberry", "watercolor blueberry",
            "watercolor cranberry", "watercolor boysenberry", "watercolor gooseberry",
            "watercolor elderberry", "watercolor mulberry", "watercolor currant",
            "watercolor lychee", "watercolor star fruit", "watercolor dragon fruit",
            "watercolor passion fruit", "watercolor guava", "watercolor papaya",
            "watercolor banana", "watercolor plantain", "watercolor tamarind",
            "watercolor jackfruit", "watercolor durian", "watercolor rambutan",
            "watercolor mangosteen", "watercolor longan"
        ]
    },
    "digital_planner": {
        "name": "Digital Planner",
        "niche": "iPad planners, GoodNotes, Notability",
        "pricing_tier": "starter_pack",
        "prompts": [
            "planner sticker checkbox", "planner sticker arrow", "planner sticker banner",
            "planner divider tab", "planner washi tape strip", "planner sticker circle",
            "planner sticker heart", "planner sticker star", "planner sticker diamond",
            "planner sticker crown", "planner sticker trophy", "planner sticker lightning",
            "planner sticker sparkle", "planner sticker flower", "planner sticker leaf",
            "planner sticker cloud", "planner sticker rain", "planner sticker sun",
            "planner sticker moon", "planner sticker planet", "planner sticker UFO",
            "planner sticker ghost", "planner sticker pumpkin", "planner sticker snowflake",
            "planner sticker gift box", "planner sticker balloon", "planner sticker flag",
            "planner sticker bookmark", "planner sticker pen", "planner sticker pencil",
            "planner sticker eraser", "planner sticker ruler", "planner sticker scissors",
            "planner sticker paper clip", "planner sticker sticky note", "planner sticker tag",
            "planner sticker label", "planner sticker frame", "planner sticker border",
            "planner sticker divider", "planner sticker header", "planner sticker bullet",
            "planner sticker asterisk", "planner sticker exclamation", "planner sticker question",
            "planner sticker plus", "planner sticker minus", "planner sticker equals",
            "planner sticker arrow right", "planner sticker arrow left"
        ]
    },
    "social_media_templates": {
        "name": "Social Media",
        "niche": "Instagram, TikTok, Pinterest",
        "pricing_tier": "mega_pack",
        "prompts": [
            "instagram story frame", "instagram post border", "tiktok overlay frame",
            "pinterest pin template", "youtube thumbnail frame", "twitter header art",
            "linkedin banner", "facebook cover frame", "instagram reel cover",
            "social media quote frame", "story highlight cover", "carousel slide frame",
            "youtube end screen", "podcast cover art", "newsletter header",
            "blog post featured image", "email header banner", "whatsapp status frame",
            "snapchat filter frame", "tumblr banner art", "reddit banner",
            "discord server icon", "twitch overlay frame", "kick stream frame",
            "social media poll frame", "testimonial card frame", "before after frame",
            "countdown timer frame", "giveaway announcement", "sale banner",
            "new arrival banner", "flash sale frame", "holiday sale frame",
            "black friday banner", "cyber monday frame", "new year sale",
            "valentines day frame", "easter sale frame", "summer sale banner",
            "back to school frame", "halloween sale frame", "thanksgiving frame",
            "christmas sale frame", "birthday sale frame", "anniversary frame",
            "grand opening frame", "product launch frame", "coming soon frame",
            "now available frame", "last chance frame"
        ]
    },
    "wedding_stationery": {
        "name": "Wedding Stationery",
        "niche": "Invites, save the dates, programs",
        "pricing_tier": "mega_pack",
        "prompts": [
            "wedding monogram wreath", "save the date frame", "wedding invitation border",
            "floral wedding arch", "wedding ring illustration", "bridal bouquet sketch",
            "wedding cake drawing", "champagne glasses toast", "wedding bell illustration",
            "wedding dove pair", "heart wedding ornament", "wedding lantern",
            "wedding candle illustration", "wedding table number frame", "place card template",
            "menu card frame", "program fan template", "thank you card frame",
            "wedding favor tag", "directions card template", "RSVP card frame",
            "wedding map illustration", "wedding venue sketch", "wedding car decoration",
            "confetti shower illustration", "rice toss illustration", "wedding sparkler",
            "wedding sparkler exit", "flower girl basket", "ring bearer pillow",
            "wedding sign illustration", "love bird illustration", "wedding bow",
            "wedding lace border", "wedding pearl border", "wedding ribbon",
            "wedding veil illustration", "wedding tiara sketch", "wedding shoe illustration",
            "wedding perfume bottle", "wedding jewelry illustration", "wedding veil",
            "wedding makeup illustration", "wedding hair illustration", "wedding dress sketch",
            "groom suit illustration", "wedding boutonniere", "wedding corsage",
            "wedding center piece", "wedding unity candle"
        ]
    },
    "nursery_wall_art": {
        "name": "Nursery Wall Art",
        "niche": "Kids room decor, baby shower gifts",
        "pricing_tier": "starter_pack",
        "prompts": [
            "cute animal alphabet", "nursery animal alphabet", "baby zoo animal",
            "nursery mountain scene", "baby hot air balloon", "nursery rainbow",
            "cute dinosaur set", "baby space rocket", "nursery woodland animals",
            "baby safari animals", "nursery farm animals", "baby ocean creatures",
            "cute bug illustrations", "nursery birds illustration", "baby butterfly",
            "nursery cloud mobile", "baby star night light", "nursery moon illustration",
            "cute bear nursery", "baby bunny illustration", "nursery fox character",
            "baby owl illustration", "nursery hedgehog", "baby squirrel illustration",
            "nursery deer illustration", "baby raccoon character", "nursery skunk cute",
            "baby possum illustration", "nursery beaver character", "baby otter illustration",
            "nursery penguin baby", "baby polar bear", "nursery seal illustration",
            "baby whale illustration", "nursery dolphin cute", "baby jellyfish pastel",
            "nursery seahorse", "baby turtle illustration", "nursery crab cute",
            "baby fish tropical", "nursery octopus cute", "baby shark illustration",
            "nursery starfish", "baby coral illustration", "nursery shell collection",
            "baby lighthouse", "nursery sailboat", "baby anchor illustration",
            "nursery compass rose", "baby map illustration"
        ]
    },
    "bullet_journal": {
        "name": "Bullet Journal",
        "niche": "BuJo spreads, habit trackers, logs",
        "pricing_tier": "starter_pack",
        "prompts": [
            "habit tracker frame", "mood tracker frame", "sleep tracker frame",
            "water tracker frame", "gratitude log frame", "daily log header",
            "weekly spread header", "monthly calendar frame", "year at a glance",
            "future log frame", "brain dump frame", "daily journal prompt",
            "weekly review frame", "monthly review frame", "goals tracker",
            "savings tracker frame", "reading log frame", "movie tracker frame",
            "meal planner frame", "workout tracker frame", "self care tracker",
            "anxiety tracker frame", "stress tracker frame", "energy tracker frame",
            "productivity tracker", "time tracker frame", "project tracker",
            "password tracker frame", "contact list frame", "birthday tracker",
            "anniversary tracker", "holiday tracker frame", "travel bucket list",
            "bucket list frame", "vision board frame", "word of the year",
            "theme tracker frame", "collection page frame", "doodle prompt frame",
            "quote page frame", "brainstorm frame", "idea tracker frame",
            "content calendar", "social media planner", "blog planner frame",
            "freelance tracker frame", "client tracker frame", "invoice tracker",
            "expense tracker frame", "income tracker frame"
        ]
    },
    "seasonal_holiday": {
        "name": "Seasonal & Holiday",
        "niche": "Year-round seasonal products",
        "pricing_tier": "mega_pack",
        "prompts": [
            "spring flowers arrangement", "spring butterfly", "spring bird nest",
            "summer beach scene", "summer ice cream truck", "summer popsicle",
            "autumn leaves wreath", "autumn pumpkin patch", "autumn acorn collection",
            "winter snowflake", "winter cozy cabin", "winter hot cocoa",
            "valentines heart frame", "valentines card topper", "valentines bow",
            "easter egg pattern", "easter bunny illustration", "easter basket",
            "st patricks clover", "st patricks pot of gold", "st patricks rainbow",
            "memorial day flag", "memorial day ribbon", "memorial day wreath",
            "independence day fireworks", "independence day flag", "independence day bunting",
            "labor day tools", "labor day hard hat", "labor day banner",
            "halloween pumpkin", "halloween ghost", "halloween bat swarm",
            "halloween spider web", "halloween witch hat", "halloween candy",
            "thanksgiving turkey", "thanksgiving cornucopia", "thanksgiving pie",
            "christmas tree", "christmas ornament", "christmas wreath",
            "christmas stocking", "christmas candy cane", "christmas gingerbread",
            "new year fireworks", "new year confetti", "new year champagne",
            "hanukkah menorah", "hanukkah dreidel", "hanukkah gift",
            "kwanzaa candle", "kwanzaa unity cup", "kwanzaa corn"
        ]
    },
    "meme_templates": {
        "name": "Meme Templates",
        "niche": "Social media content, viral marketing",
        "pricing_tier": "starter_pack",
        "prompts": [
            "distracted boyfriend meme", "woman yelling at cat meme", "this is fine meme",
            "drake meme template", "expanding brain meme", "change my mind meme",
            "uno reverse card meme", "surprised pikachu meme", "stonks meme",
            "waiting skeleton meme", "two buttons meme", "left exit 12 meme",
            "boardroom meeting meme", "brain size meme", "clown applying makeup",
            "falling stairs meme", "hidden pain meme", "big brain meme",
            "galaxy brain meme", "smooth brain meme", "pepe hands meme",
            "wojak mask meme", "chad vs virgin meme", "gigachad meme",
            "doomer vs bloomER meme", "NPC meme template", "blue pill red pill",
            "matrix meme", "hackerman meme", "science rules meme",
            "bait meme template", "copium meme", "hopium meme",
            "amogus meme", "sus meme template", "among us crewmate",
            "minecraft steve meme", "fortnite default dance", "roblox oof",
            "gaming chair meme", "pc master race meme", "console peasant meme",
            "phone bad book good meme", "ok boomer meme", "karen haircut meme",
            "manager meme", "speak to manager meme", "wine aunt meme",
            "doge meme 2024", "cheems meme template"
        ]
    },
    "ui_icons": {
        "name": "UI & Icons",
        "niche": "App design, web design, presentations",
        "pricing_tier": "starter_pack",
        "prompts": [
            "home icon set", "settings gear icon", "user profile icon",
            "search magnifying glass", "mail envelope icon", "phone icon",
            "chat bubble icon", "notification bell icon", "lock security icon",
            "unlock icon", "heart favorite icon", "star rating icon",
            "share icon set", "download arrow icon", "upload cloud icon",
            "trash delete icon", "edit pencil icon", "plus add icon",
            "minus remove icon", "checkmark success icon", "x close icon",
            "arrow left right icons", "menu hamburger icon", "close x icon",
            "refresh reload icon", "pause play icon", "stop square icon",
            "volume speaker icon", "mute icon", "camera icon",
            "photo image icon", "video play icon", "music note icon",
            "file document icon", "folder icon", "bookmark icon",
            "calendar date icon", "clock time icon", "map pin location icon",
            "globe world icon", "wifi signal icon", "bluetooth icon",
            "battery icon set", "signal bars icon", "usb icon",
            "link chain icon", "eye visibility icon", "hidden eye icon",
            "filter funnel icon", "sort icon set"
        ]
    },
    "food_illustrations": {
        "name": "Food Illustrations",
        "niche": "Restaurant branding, recipe blogs, menus",
        "pricing_tier": "starter_pack",
        "prompts": [
            "pizza slice illustration", "burger and fries", "taco illustration",
            "sushi platter drawing", "ramen bowl illustration", "pasta plate drawing",
            "fried chicken bucket", "hot dog illustration", "sandwich stack drawing",
            "donut glaze illustration", "cookie stack drawing", "cake slice illustration",
            "cupcake decoration", "pie chart food pun", "pancake stack drawing",
            "waffle illustration", "cereal bowl drawing", "toast with avocado",
            "smoothie bowl illustration", "juice glass drawing", "coffee cup latte art",
            "tea cup illustration", "bubble tea drawing", "milkshake illustration",
            "ice cream sundae", "popsicle illustration", "candy wrapper drawing",
            "chocolate bar illustration", "lollipop swirl drawing", "gumdrop illustration",
            "apple illustration", "banana bunch drawing", "orange slice cross-section",
            "grape cluster illustration", "strawberry with leaves", "blueberry illustration",
            "watermelon slice drawing", "pineapple cross-section", "coconut illustration",
            "mango slice illustration", "peach drawing", "pear illustration",
            "cherry pair illustration", "lemon slice drawing", "lime illustration",
            "avocado cross-section", "corn illustration", "carrot drawing",
            "broccoli illustration", "tomato slice drawing"
        ]
    },
    "animal_cartoons": {
        "name": "Animal Cartoons",
        "niche": "Kids products, stickers, apparel",
        "pricing_tier": "mega_pack",
        "prompts": [
            "cute cat sitting", "happy dog cartoon", "bunny rabbit illustration",
            "baby chick drawing", "baby duck illustration", "baby lamb cartoon",
            "baby goat drawing", "baby cow illustration", "baby pig cartoon",
            "baby horse drawing", "baby donkey illustration", "baby elephant cartoon",
            "baby giraffe drawing", "baby zebra illustration", "baby lion cartoon",
            "baby tiger drawing", "baby leopard illustration", "baby cheetah cartoon",
            "baby bear drawing", "baby panda illustration", "baby koala cartoon",
            "baby sloth drawing", "baby monkey illustration", "baby chimpanzee cartoon",
            "baby kangaroo drawing", "baby koala illustration", "baby wombat cartoon",
            "baby platypus drawing", "baby penguin illustration", "baby seal cartoon",
            "baby otter drawing", "baby beaver illustration", "baby raccoon cartoon",
            "baby fox drawing", "baby wolf illustration", "baby deer cartoon",
            "baby moose drawing", "baby reindeer illustration", "baby owl cartoon",
            "baby eagle drawing", "baby hawk illustration", "baby parrot cartoon",
            "baby flamingo drawing", "baby pelican illustration", "baby swan cartoon",
            "baby peacock drawing", "baby dove illustration", "baby robin cartoon",
            "baby hummingbird drawing", "baby woodpecker illustration"
        ]
    },
    "abstract_patterns": {
        "name": "Abstract & Patterns",
        "niche": "Backgrounds, textures, branding",
        "pricing_tier": "mega_pack",
        "prompts": [
            "geometric pattern seamless", "boho pattern repeat", "minimalist line pattern",
            "marble texture abstract", "gradient mesh background", "noise texture overlay",
            "halftone dot pattern", "wave pattern seamless", "zigzag pattern repeat",
            "chevron pattern seamless", "diamond pattern repeat", "hexagon pattern",
            "triangle pattern seamless", "circle pattern repeat", "organic blob pattern",
            "terrazzo pattern seamless", "confetti pattern repeat", "starry sky pattern",
            "constellation pattern", "cloud pattern seamless", "wave pattern minimalist",
            "mountain silhouette pattern", "forest pattern seamless", "desert dune pattern",
            "ocean wave pattern", "coral reef pattern", "underwater pattern",
            "space nebula pattern", "galaxy swirl pattern", "aurora borealis pattern",
            "sunrise gradient pattern", "sunset gradient pattern", "midnight blue pattern",
            "pastel gradient pattern", "neon glow pattern", "earth tone pattern",
            "forest green pattern", "ocean blue pattern", "desert sand pattern",
            "volcanic red pattern", "arctic white pattern", "tropical green pattern",
            "autumn orange pattern", "spring pink pattern", "winter gray pattern",
            "summer yellow pattern", "rustic brown pattern", "industrial gray pattern",
            "vintage cream pattern", "modern black pattern"
        ]
    }
}

def get_all_prompts():
    """Flatten all prompts across categories."""
    all_prompts = []
    for cat_key, cat_data in CATEGORIES.items():
        for prompt in cat_data["prompts"]:
            all_prompts.append({
                "category": cat_key,
                "category_name": cat_data["name"],
                "niche": cat_data["niche"],
                "pricing_tier": cat_data["pricing_tier"],
                "prompt": prompt
            })
    return all_prompts

def get_category(category_key):
    """Get a specific category."""
    return CATEGORIES.get(category_key)

def get_random_category():
    """Get a random category."""
    import random
    return random.choice(list(CATEGORIES.keys()))

def get_prompts_for_category(category_key, count=50):
    """Get specific number of prompts for a category."""
    cat = CATEGORIES.get(category_key, {})
    return cat.get("prompts", [])[:count]
