// Menu item metadata - images, descriptions, nutrition
// Keys match item.id from backend (item-1 to item-10)

export const menuMeta = {
    'item-1': {
        image: 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop',
        desc_kz: 'Дәстүрлі орыс сорпасы, қызылша және көкөністермен',
        desc_ru: 'Традиционный свекольный суп с овощами',
        desc_en: 'Traditional beet soup with vegetables',
        kcal: 45, protein: 1.5, fat: 1.8, carbs: 5.5
    },
    'item-2': {
        image: 'https://images.unsplash.com/photo-1583577612013-4fecf7bf8f13?w=400&h=300&fit=crop',
        desc_kz: 'Қой етінен дайындалған дәстүрлі сорпа',
        desc_ru: 'Традиционный суп из баранины с овощами',
        desc_en: 'Traditional lamb soup with vegetables',
        kcal: 55, protein: 3.5, fat: 2.8, carbs: 4.2
    },
    'item-3': {
        image: 'https://images.unsplash.com/photo-1596097635121-14b63b7a0c19?w=400&h=300&fit=crop',
        desc_kz: 'Өзбек тәсілімен дайындалған плов',
        desc_ru: 'Узбекский плов с мясом и морковью',
        desc_en: 'Uzbek pilaf with meat and carrots',
        kcal: 180, protein: 6.5, fat: 8.5, carbs: 22
    },
    'item-4': {
        image: 'https://images.unsplash.com/photo-1529042410759-befb1204b468?w=400&h=300&fit=crop',
        desc_kz: 'Үй жасалған котлет, гарнирмен',
        desc_ru: 'Домашняя котлета с гарниром',
        desc_en: 'Homemade cutlet with side dish',
        kcal: 220, protein: 15, fat: 14, carbs: 8
    },
    'item-5': {
        image: 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=400&h=300&fit=crop',
        desc_kz: 'Буланған ақ күріш',
        desc_ru: 'Отварной белый рис',
        desc_en: 'Steamed white rice',
        kcal: 130, protein: 2.7, fat: 0.3, carbs: 28
    },
    'item-6': {
        image: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop',
        desc_kz: 'Жаңа көкөністерден жасалған салат',
        desc_ru: 'Свежий овощной салат',
        desc_en: 'Fresh vegetable salad',
        kcal: 35, protein: 1.2, fat: 0.2, carbs: 7
    },
    'item-7': {
        image: 'https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=400&h=300&fit=crop',
        desc_kz: 'Жеміс компоты',
        desc_ru: 'Фруктовый компот',
        desc_en: 'Fruit compote drink',
        kcal: 40, protein: 0.1, fat: 0, carbs: 10
    },
    'item-8': {
        image: 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400&h=300&fit=crop',
        desc_kz: 'Ыстық шай',
        desc_ru: 'Горячий чай',
        desc_en: 'Hot tea',
        kcal: 0, protein: 0, fat: 0, carbs: 0
    },
    'item-9': {
        image: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop',
        desc_kz: 'Балмұздақ пирожок',
        desc_ru: 'Пирожок с начинкой',
        desc_en: 'Stuffed pastry',
        kcal: 290, protein: 5.5, fat: 12, carbs: 38
    },
    'item-10': {
        image: 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&h=300&fit=crop',
        desc_kz: 'Жаңа піскен булочка',
        desc_ru: 'Свежая булочка',
        desc_en: 'Fresh bun',
        kcal: 310, protein: 7, fat: 8, carbs: 52
    }
};

// Placeholder image for items without metadata
export const placeholderImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop';

// Get metadata for item (by id or name fallback)
export function getItemMeta(item) {
    return menuMeta[item.id] || null;
}
