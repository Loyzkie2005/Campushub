/**
 * Client-side autocomplete ranking — no API.
 * Order: exact → prefix → token → contains → fuzzy (Levenshtein).
 */
(function (global) {
    function levenshtein(a, b, maxDistance) {
        maxDistance = maxDistance == null ? 2 : maxDistance;
        if (a === b) return 0;
        if (!a.length) return b.length;
        if (!b.length) return a.length;
        if (Math.abs(a.length - b.length) > maxDistance) return maxDistance + 1;

        var prev = [];
        var curr = [];
        var i, j, cost, del, ins, sub, v, rowMin;
        for (i = 0; i <= b.length; i++) prev[i] = i;

        for (i = 1; i <= a.length; i++) {
            curr[0] = i;
            rowMin = curr[0];
            for (j = 1; j <= b.length; j++) {
                cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
                del = prev[j] + 1;
                ins = curr[j - 1] + 1;
                sub = prev[j - 1] + cost;
                v = del < ins ? del : ins;
                if (sub < v) v = sub;
                curr[j] = v;
                if (v < rowMin) rowMin = v;
            }
            if (rowMin > maxDistance) return maxDistance + 1;
            for (j = 0; j <= b.length; j++) prev[j] = curr[j];
        }
        return prev[b.length];
    }

    function scoreText(text, query) {
        if (!text || !query) return 0;
        var t = String(text).trim().toLowerCase();
        var q = String(query).trim().toLowerCase();
        if (!t || !q) return 0;
        if (t === q) return 1000;
        if (t.indexOf(q) === 0) return 800 + q.length * 2;

        var tokens = t.split(/[\s\-_/.,]+/).filter(Boolean);
        var i, d;
        for (i = 0; i < tokens.length; i++) {
            if (tokens[i] === q) return 700;
            if (tokens[i].indexOf(q) === 0) return 650 + q.length;
        }
        if (t.indexOf(q) !== -1) return 400 + q.length;

        if (q.length >= 2 && q.length <= 12) {
            for (i = 0; i < tokens.length; i++) {
                if (Math.abs(tokens[i].length - q.length) > 2) continue;
                d = levenshtein(tokens[i], q, 2);
                if (d === 1) return 280;
                if (d === 2) return 180;
            }
            if (t.length <= 16) {
                d = levenshtein(t, q, 2);
                if (d === 1) return 250;
                if (d === 2) return 150;
            }
        }
        return 0;
    }

    function suggest(items, query, limit) {
        limit = limit == null ? 8 : limit;
        var list = Array.isArray(items) ? items : [];
        var q = String(query || '').trim().toLowerCase();
        if (!list.length) return [];
        if (!q) return list.slice(0, limit);

        var scored = [];
        for (var i = 0; i < list.length; i++) {
            var item = list[i];
            var text = typeof item === 'string' ? item : String(item);
            var score = scoreText(text, q);
            if (score > 0) scored.push({ item: item, score: score, key: text.toLowerCase() });
        }
        scored.sort(function (a, b) {
            if (b.score !== a.score) return b.score - a.score;
            return a.key < b.key ? -1 : a.key > b.key ? 1 : 0;
        });
        return scored.slice(0, limit).map(function (row) { return row.item; });
    }

    // Keep in sync with campushub/.../form_suggestion_samples.dart
    // Add names here to make them appear in Product Name suggestions.
    var PRODUCT_NAME_SAMPLES = [
        // Beverages
        'MilkTea', 'Brown Sugar MilkTea', 'Taro MilkTea', 'Matcha MilkTea',
        'Wintermelon MilkTea', 'Okinawa MilkTea', 'Thai Tea',
        'Milkshake', 'Chocolate Milkshake', 'Strawberry Milkshake',
        'Oreo Milkshake', 'Vanilla Milkshake',
        'Iced Coffee', 'Hot Coffee', 'Americano', 'Cafe Latte', 'Cappuccino',
        'Espresso', 'Mocha', 'Caramel Macchiato', 'Cold Brew', 'Frappe',
        'Iced Tea', 'Lemon Iced Tea', 'Green Tea', 'Hot Chocolate',
        'Bottled Water', 'Mineral Water', 'Soft Drink', 'Cola', 'Sprite',
        'Royal', 'Mountain Dew', 'Juice', 'Orange Juice', 'Apple Juice',
        'Mango Juice', 'Pineapple Juice', 'Calamansi Juice', 'Buko Juice',
        'Sago Gulaman', 'Fruit Shake', 'Mango Shake', 'Avocado Shake',
        'Smoothie', 'Yakult', 'Energy Drink', 'Sports Drink', 'Soy Milk',
        'Chocolate Drink',
        // Rice / silog
        'Garlic Rice', 'Plain Rice', 'Java Rice',
        'Tapsilog', 'Tocilog', 'Longsilog', 'Hotsilog', 'Bangsilog',
        'Chickensilog', 'Cornsilog', 'Spamsilog',
        'Adobo Rice', 'Chicken Adobo', 'Pork Adobo', 'Sinigang Rice',
        'Kare-Kare Rice', 'Bicol Express Rice', 'Caldereta Rice',
        'Menudo Rice', 'Afritada Rice', 'Beef Steak Rice', 'Pork Steak Rice',
        'Sisig Rice', 'Chicken Sisig', 'Pork Sisig',
        'Lechon Kawali Rice', 'Crispy Pata Rice', 'Fried Bangus Rice',
        'Tinapa Rice', 'Daing Rice', 'Tinola Rice', 'Nilaga Rice', 'Bulalo Rice',
        'Pares', 'Beef Pares', 'Lomi', 'Mami', 'Batchoy', 'Goto',
        'Arroz Caldo', 'Champorado', 'Lugaw', 'Congee',
        // Noodles / pasta
        'Pancit Canton', 'Pancit Bihon', 'Pancit Palabok', 'Pancit Malabon',
        'Pancit Sotanghon', 'Carbonara', 'Spaghetti', 'Filipino Spaghetti',
        'Baked Macaroni', 'Lasagna', 'Ramen', 'Instant Noodles', 'Cup Noodles',
        'Sotanghon Soup', 'Misua',
        // Sandwiches / burgers
        'Burger', 'Cheese Burger', 'Chicken Burger', 'Double Burger',
        'Hotdog', 'Cheese Hotdog', 'Footlong',
        'Chicken Sandwich', 'Club Sandwich', 'Egg Sandwich', 'Ham Sandwich',
        'Tuna Sandwich', 'Bacon Egg Sandwich',
        'Siopao', 'Asado Siopao', 'Bola-Bola Siopao',
        'Siomai', 'Siomai Rice', 'Pork Siomai', 'Chicken Siomai', 'Beef Siomai',
        'Dumplings', 'Gyoza',
        // Fried / grilled
        'Fried Chicken', 'Chicken Wings', 'Chicken Nuggets', 'Chicken Fillet',
        'Chicken Poppers', 'Pork BBQ', 'Chicken BBQ',
        'Isaw', 'Betamax', 'Adidas', 'Fish Ball', 'Kikiam', 'Squid Ball',
        'Kwek-Kwek', 'Tokneneng', 'Calamares',
        'French Fries', 'Cheese Fries', 'Onion Rings', 'Mozzarella Sticks',
        'Tempura', 'Chicken Skin', 'Chicharon',
        // Snacks / street food
        'Lumpia', 'Shanghai Lumpia', 'Vegetable Lumpia',
        'Turon', 'Banana Cue', 'Kamote Cue', 'Corn on the Cob', 'Mais', 'Maruya',
        'Banana Chips', 'Potato Chips', 'Corn Chips', 'Nachos', 'Popcorn',
        'Crackers', 'Biscuits', 'Cookies', 'Wafer', 'Pretzels', 'Nuts',
        'Trail Mix', 'Candy', 'Chocolate Bar', 'Gummy Candy', 'Lollipop',
        'Marshmallow', 'Piattos', 'Chippy', 'Nova', 'Boy Bawang', 'Clover Chips',
        // Desserts / baked
        'Cupcake', 'Donut', 'Glazed Donut', 'Chocolate Donut', 'Muffin',
        'Brownie', 'Cookie', 'Chocolate Chip Cookie',
        'Puto', 'Puto Bumbong', 'Kutsinta', 'Biko', 'Suman', 'Bibingka',
        'Ensaymada', 'Pandesal', 'Spanish Bread', 'Cheese Bread', 'Ube Bread',
        'Croissant', 'Danish', 'Cake Slice', 'Ube Cake', 'Chocolate Cake',
        'Cheesecake', 'Halo-Halo', 'Ice Cream', 'Ice Cream Cone', 'Sundae',
        'Fruit Salad', 'Buko Pandan', 'Leche Flan', 'Maja Blanca',
        'Ginataang Bilo-Bilo', 'Taho', 'Yema', 'Polvoron', 'Pastillas',
        // Pizza / international
        'Pizza Slice', 'Hawaiian Pizza', 'Pepperoni Pizza', 'Cheese Pizza',
        'Shawarma', 'Chicken Shawarma', 'Beef Shawarma',
        'Tacos', 'Burrito', 'Quesadilla',
        'Sushi Roll', 'California Roll', 'Kimbap', 'Bibimbap', 'Pad Thai',
        'Fried Rice', 'Yang Chow Fried Rice', 'Kimchi Fried Rice',
        'Curry Rice', 'Chicken Curry', 'Beef Curry', 'Samosa', 'Spring Rolls',
        'Waffle', 'Pancake', 'French Toast', 'Omelette', 'Scrambled Eggs',
        'Breakfast Plate',
        // Combos
        'Combo Meal A', 'Combo Meal B', 'Combo Meal C',
        'Student Meal', 'Value Meal', 'Rice Meal Combo', 'Burger Combo',
        'Chicken Combo', 'Snack Pack', 'Drink + Snack',
        // School supplies
        'Notebook', 'Ballpen', 'Pencil', 'Mechanical Pencil', 'Eraser',
        'Sharpener', 'Highlighter', 'Marker', 'Correction Tape', 'Stapler',
        'Paper Clip', 'Binder', 'Folder', 'Clear Book', 'Index Card',
        'Bond Paper', 'Intermediate Pad', 'Yellow Pad', 'Ruler', 'Calculator',
        'USB Flash Drive', 'ID Lace', 'ID Holder', 'Backpack', 'Tote Bag',
        'Lunch Box', 'Water Bottle', 'Umbrella',
        // Merch / misc
        'School Shirt', 'Campus Hoodie', 'Campus Cap', 'Lanyard',
        'Sticker Pack', 'Keychain', 'Tumbler', 'Mug', 'Phone Case',
        'Earphones', 'Power Bank', 'Face Mask', 'Hand Sanitizer',
        'Tissue Pack', 'Wet Wipes'
    ];

    global.LocalAutocomplete = {
        suggest: suggest,
        scoreText: scoreText,
        PRODUCT_NAME_SAMPLES: PRODUCT_NAME_SAMPLES
    };
})(window);
