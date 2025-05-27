import sys
import io
import json
from datetime import datetime
from pathlib import Path
from benders import (Bender, WaterBender, FireBender, EarthBender, AirBender, EnergyBender, 
                     Element, BendingStyle, Item, Equipment, Ability, ItemRarity, choose_bender) # choose_bender eklendi

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SAVE_FILE = "benders_save.json"
# STORY_FILE = "story_progress.json" # game.py içinde yönetiliyor

def save_bender_data(bender):
    try:
        all_data = {}
        if Path(SAVE_FILE).exists():
            with open(SAVE_FILE, "r", encoding='utf-8') as f:
                try:
                    all_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Uyarı: {SAVE_FILE} dosyası bozuk, yeni kayıt oluşturulacak.")
                    all_data = {} # Bozuksa sıfırla
        
        all_data[bender.name] = bender.to_dict() # Bender sınıfındaki to_dict metodunu kullan
        all_data[bender.name]["saved_at"] = str(datetime.now())
        
        with open(SAVE_FILE, "w", encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        print(f"'{bender.name}' verileri kaydedildi.")    
    except Exception as e:
        print(f"Kayıt hatası: {e}")

def load_bender_list_names():
    try:
        if not Path(SAVE_FILE).exists():
            return []
            
        with open(SAVE_FILE, "r", encoding='utf-8') as f:
            all_data = json.load(f)
            # Kayıt zamanına göre de sıralama eklenebilir veya sadece isme göre
            return sorted(all_data.keys(), 
                        key=lambda x: all_data[x].get("level", 0), 
                        reverse=True)
    except Exception as e:
        print(f"Karakter listesi yükleme hatası: {e}")
        return []

def load_bender_data(name):
    try:
        if not Path(SAVE_FILE).exists():
            print(f"{SAVE_FILE} bulunamadı.")
            return None
            
        with open(SAVE_FILE, "r", encoding='utf-8') as f:
            all_data = json.load(f)
            data = all_data.get(name)
            if data:
                style_enum_name = data.get("bending_style") 
                element_name_from_save = data.get("element") 
                processed_bending_style_arg = None
                if style_enum_name and element_name_from_save:
                    suffix_to_remove = "_" + element_name_from_save.upper()
                    if style_enum_name.endswith(suffix_to_remove):
                        processed_bending_style_arg = style_enum_name[:-len(suffix_to_remove)].lower()
                    else: 
                        # Eğer stil adı element içermiyorsa (örn: EnergyBender'da stil yok veya eski kayıt)
                        # Ya da BendingStyle enum'ları sadece stil adını içeriyorsa (örn: FLIGHT)
                        # Bu durumda Bender sınıfının __init__'i BendingStyle[f"{STYLE}_{ELEMENT}"] yapısını kurar.
                        # choose_bender'a sadece stilin kendisini (örn: "flight") yollamak yeterli.
                        # Bu senaryo için style_enum_name'i direkt lower() ile yollayabiliriz,
                        # choose_bender ve Bender.__init__ bunu yönetmeli.
                        # Örn: BendingStyle.FLIGHT_AIR -> style_enum_name = "FLIGHT_AIR"
                        # processed_bending_style_arg = "flight" olmalı.
                        # Bender.__init__ (..., "air", "flight") -> BendingStyle["FLIGHT_AIR"]
                        # Mevcut suffix_to_remove mantığı "FLIGHT_AIR" -> "FLIGHT" -> "flight" yapar, bu doğru.
                        # Eğer sadece "FLIGHT" kaydedilmiş olsaydı (yanlışlıkla):
                        # processed_bending_style_arg = "flight" olurdu, bu da doğru çalışır.
                        # Sorun yok gibi.
                         pass # processed_bending_style_arg None kalırsa choose_bender stilsiz oluşturur. Veya:
                    if not processed_bending_style_arg and style_enum_name: # Eğer suffix eşleşmediyse ama stil varsa
                        # Belki stil adı element içermiyor, direkt kullanmayı dene
                        # Örn: stil "FLIGHT" olarak kaydedilmişse (yanlışlıkla)
                        # choose_bender("Aang", "air", "flight") -> AirBender("Aang", "flight") -> super(..., "flight")
                        # Bender(..., "air", "flight") -> BendingStyle["FLIGHT_AIR"] -> Doğru.
                        # O zaman style_enum_name.lower() yeterli olurdu.
                        # Ama biz .name (örn: FLIGHT_AIR) kaydettiğimiz için yukarıdaki suffix mantığı daha doğru.
                        # Eğer suffix ile ayrıştırma başarısız olduysa bir fallback:
                        parts = style_enum_name.split('_')
                        if len(parts) > 0 : # En azından bir parça varsa
                             # Genelde ilk kısım stilin ana adıdır (örn: NORTHERN_WATER -> NORTHERN)
                             # SUN_WARRIOR_FIRE -> SUN (Bu yanlış olur, SUN_WARRIOR lazım)
                             # Bu yüzden suffix_to_remove daha güvenli.
                             # Eğer o çalışmazsa, belki kayıt bozuktur veya format farklıdır.
                             # Şimdilik suffix'e güvenelim.
                             pass


                bender = choose_bender(data["name"], data["element"].lower(), processed_bending_style_arg)

                # Temel statları ve seviyeyi yükle
                bender.level = data.get("level", 1)
                bender.experience = data.get("experience", 0)
                bender.gold = data.get("gold", 100)
                bender.reputation = data.get("reputation", 0)
                bender.train_count = data.get("train_count", 0)
                bender.stat_points = data.get("stat_points", 0)

                # Bender.__init__ içinde base statlar ayarlanıyor.
                # Sonra update_stats_from_equipment çağrılıyor.
                # Kaydedilmiş base statları yüklemek daha doğru olabilir.
                bender.base_max_health = data.get("base_max_health", bender.base_max_health)
                bender.base_power = data.get("base_power", bender.base_power)
                bender.base_max_energy = data.get("base_max_energy", bender.base_max_energy)
                
                # Yetenekleri yükle (Ability nesneleri olarak)
                loaded_abilities = []
                raw_abilities_data = data.get("abilities", [])
                if raw_abilities_data and isinstance(raw_abilities_data[0], dict):
                    for ab_data in raw_abilities_data:
                        # current_cooldown gibi eksik olabilecek alanlar için .get() kullan
                        ability = Ability(
                            name=ab_data["name"],
                            description=ab_data["description"],
                            effect_type=ab_data["effect_type"],
                            effect_amount=ab_data["effect_amount"],
                            energy_cost=ab_data["energy_cost"],
                            is_active=ab_data.get("is_active", True),
                            cooldown=ab_data.get("cooldown", 0),
                            current_cooldown=ab_data.get("current_cooldown", 0),
                            target_type=ab_data.get("target_type", "opponent")
                        )
                        loaded_abilities.append(ability)
                    bender.abilities = loaded_abilities # Üzerine yaz, _get_initial_abilities'den gelenleri değil bunları kullan
                    bender.active_abilities = [a for a in bender.abilities if a.is_active]
                    bender.passive_abilities = [a for a in bender.abilities if not a.is_active]
                
                # Envanteri yükle
                bender.inventory = []
                for item_data in data.get("inventory", []):
                    rarity_name = item_data.get("rarity", "COMMON")
                    actual_rarity = ItemRarity[rarity_name] if hasattr(ItemRarity, rarity_name) else ItemRarity.COMMON
                    
                    if item_data.get("slot"): 
                        item = Equipment(
                            name=item_data["name"], description=item_data["description"],
                            effect_type=item_data["effect_type"], effect_amount=item_data["effect_amount"],
                            slot=item_data["slot"], price=item_data.get("price", 0),
                            rarity=actual_rarity, 
                            durability=item_data.get("durability", 100) 
                        )
                    else: 
                        item = Item(
                            name=item_data["name"], description=item_data["description"],
                            effect_type=item_data["effect_type"], effect_amount=item_data["effect_amount"],
                            price=item_data.get("price", 0), 
                            usage_limit=item_data.get("usage_limit", 1),
                            rarity=actual_rarity
                        )
                    bender.inventory.append(item)

                # Kuşanılmış ekipmanları yükle
                bender.equipped_items = []
                for eq_data in data.get("equipped_items", []):
                    rarity_name = eq_data.get("rarity", "COMMON")
                    actual_rarity = ItemRarity[rarity_name] if hasattr(ItemRarity, rarity_name) else ItemRarity.COMMON
                    eq = Equipment(
                        name=eq_data["name"], description=eq_data["description"],
                        effect_type=eq_data["effect_type"], effect_amount=eq_data["effect_amount"],
                        slot=eq_data["slot"], price=eq_data.get("price", 0),
                        rarity=actual_rarity, 
                        durability=eq_data.get("durability", 100)
                    )
                    bender.equipped_items.append(eq) # Sadece listeye ekle, equip() çağırma

                # Statları ve etkileri en son güncelle (ekipmanlar yüklendikten sonra)
                bender.update_stats_from_equipment()

                # Kaydedilmiş anlık can ve enerjiyi yükle (update_stats'tan sonra)
                bender.health = data.get("health", bender.max_health)
                bender.energy = data.get("energy", bender.max_energy)
                # Diğer anlık statlar (crit_chance, dodge_chance) update_stats ile zaten hesaplanıyor.
                # Ama eğer buff/debuff ile anlık değişmişse ve o da kaydedildiyse, onlar da yüklenebilir.
                # Şimdilik crit ve dodge'ı update_stats'a bırakalım.
                # Eğer base crit/dodge da kaydedilmişse (to_dict'te yok ama eklenebilir), onlar da yüklenebilir.
                # bender.crit_chance = data.get("crit_chance", bender.crit_chance)
                # bender.dodge_chance = data.get("dodge_chance", bender.dodge_chance)

                # Buff ve Debuff'ları yükle (eğer kaydedildiyse)
                bender.buffs = data.get("buffs", {})
                bender.debuffs = data.get("debuffs", {})
                # Yükleme sonrası bu buff/debuff'ların etkilerini tekrar uygulamak gerekebilir
                # veya update_stats_from_equipment bunları zaten hesaba katmalı.
                # Şimdilik tick_buffs_debuffs'in bunları yönettiğini varsayalım.

                loaded_special_abilities = []
                for style_name in data.get("special_abilities_unlocked", []):
                    if hasattr(BendingStyle, style_name):
                        loaded_special_abilities.append(BendingStyle[style_name])
                bender.special_abilities_unlocked = loaded_special_abilities
                
                # Hikaye ilerlemesi gibi diğer veriler
                # bender.story_progress = data.get("story_progress", 0) # Eğer Bender sınıfında varsa

                print(f"'{name}' karakteri başarıyla yüklendi.")
                return bender
            else:
                print(f"'{name}' adında kayıtlı karakter bulunamadı.")
            return None
    except FileNotFoundError:
        print(f"Kayıt dosyası ({SAVE_FILE}) bulunamadı.")
        return None
    except json.JSONDecodeError:
        print(f"Kayıt dosyası ({SAVE_FILE}) bozuk veya geçersiz JSON formatında.")
        return None
    except Exception as e:
        print(f"Yükleme hatası ({name}): {e}")
        import traceback
        traceback.print_exc() # Detaylı hata için
        return None

# story_progress game.py içinde yönetildiği için buradaki fonksiyonlar kaldırıldı veya game.py'ye taşındı.

def get_leaderboard():
    try:
        if not Path(SAVE_FILE).exists():
            return []
            
        with open(SAVE_FILE, "r", encoding='utf-8') as f:
            all_data = json.load(f)
            leaderboard = []
            
            for name, data in all_data.items():
                level = data.get("level", 1)
                # Güç bilgisi doğrudan bender.power olarak kaydediliyor, base_power değil.
                power = data.get("power", data.get("base_power", 0) + (data.get("level",1)-1)*5 ) # Yaklaşık bir değer
                reputation = data.get("reputation", 0)
                element = data.get("element", "Bilinmiyor")
                
                leaderboard.append((name, level, power, reputation, element))
            
            return sorted(
                leaderboard,
                key=lambda x: (-x[1], -x[2], -x[3]) # Seviye, sonra güç, sonra itibar (azalan)
            )[:10] # İlk 10
    except Exception as e:
        print(f"Liderlik tablosu yüklenirken hata: {e}")
        return []