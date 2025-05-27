import random
import time
import json
import os # save_game ve load_game için dosya yolu kontrolü
from pathlib import Path # save_game ve load_game için

from benders import (WaterBender, FireBender, EarthBender, 
                    AirBender, EnergyBender, choose_bender,
                    Element, BendingStyle, Item, Equipment, Ability, ItemRarity)

# data.py içeriği (eğer ayrı bir dosya yoksa buraya eklenebilir)
# Ancak story_progress.json için kendi fonksiyonları var, bu iyi.
STORY_FILE = "story_progress.json" # game.py kendi hikaye dosyasını yönetsin

def save_story_progress(progress_data):
    try:
        with open(STORY_FILE, "w", encoding='utf-8') as f: # utf-8 eklendi
            json.dump(progress_data, f, indent=4, ensure_ascii=False) # ensure_ascii=False eklendi
    except Exception as e:
        print(f"Hikaye kayıt hatası: {e}")

def load_story_progress():
    try:
        if not Path(STORY_FILE).exists(): # Path ile kontrol
            return {}
            
        with open(STORY_FILE, "r", encoding='utf-8') as f: # utf-8 eklendi
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Uyarı: {STORY_FILE} dosyası bozuk veya boş, yeni ilerleme oluşturulacak.")
        return {} 
    except Exception as e:
        print(f"Hikaye yükleme hatası: {e}")
        return {}
    
special_event_chance = 20 # Bu bir yüzde olarak kullanılabilir, örn: if random.randint(1,100) <= special_event_chance:

def random_city_event(player_obj): # player_obj Bender nesnesi olmalı
    """
    Şehirde rastgele bir olayı tetikler.
    Args:
        player_obj (Bender/Player): Etkilenecek oyuncu nesnesi.
    """
    print("\n--- Şehirde Rastgele Olay ---")
    event_roll = random.randint(1, 100)

    if event_roll <= 40: # %40 ihtimal
        print("Pazarda ilginç bir satıcıyla karşılaştın.")
        print("1. Eşya al (Deneme amaçlı, altın harcamaz)")
        print("2. Sohbet et (Deneyim kazan)")
        choice = input("Seçiminiz (1-2): ")
        if choice == '1':
            # Örnek bir eşya ekleme
            found_item = Item("Gizemli İksir", "Satıcıdan aldığın gizemli bir iksir.", "health", random.randint(10,30), 0, usage_limit=1, rarity=ItemRarity.UNCOMMON)
            player_obj.add_to_inventory(found_item)
            print(f"'{found_item.name}' envanterine eklendi!")
        elif choice == '2':
            xp_gain = random.randint(5, 15)
            player_obj.experience += xp_gain
            player_obj._check_level_up()
            print(f"Sohbetten yeni bilgiler öğrendin ve {xp_gain} XP kazandın.")
        else:
            print("Satıcıyla ilgilenmedin.")
    elif event_roll <= 70: # %30 ihtimal (41-70)
        print("Bir hırsızlık olayına tanık oldun!")
        print("1. Müdahale et (İtibar ve altın kazanma şansı)")
        print("2. Görmezden gel")
        choice = input("Seçiminiz (1-2): ")
        if choice == '1':
            if random.random() < 0.6: # %60 başarı şansı
                gold_reward = random.randint(20,50)
                rep_reward = random.randint(5,10)
                player_obj.gold += gold_reward
                player_obj.reputation += rep_reward
                print(f"Kahramanca müdahale ettin! {gold_reward} altın ve {rep_reward} itibar kazandın.")
            else:
                print("Müdahale etmeye çalıştın ama hırsız kaçtı. En azından denedin.")
                player_obj.reputation += 1
        else:
            print("Olay yerinden sessizce uzaklaştın.")
    else: # %30 ihtimal (71-100)
        print("Şehirde sakin bir gün geçiriyorsun ve biraz dinleniyorsun.")
        heal_amount = player_obj.max_health // 10 # Maks canın %10'u kadar iyileş
        player_obj.heal(heal_amount)
        # print(f"{heal_amount} can yeniledin.") # heal metodu zaten mesaj basıyor
    print("-----------------------------\n")

SAVE_DIR = "saves" # Kayıt dosyalarının tutulacağı klasör

def save_game(bender): # Bu fonksiyon data.py'deki save_bender_data ile çok benzer
                    # Eğer main.py data.py'yi kullanıyorsa bu fonksiyon gereksiz olabilir
                    # Ya da bu daha detaylıysa bu kullanılmalı. Şimdilik bırakıyorum.
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    # Bender.to_dict() metodunu kullanalım (benders.py'ye eklenmiş olmalı)
    # Bu, data.py'deki save_bender_data ile aynı mantığı kullanır.
    data_to_save = bender.to_dict()

    file_path = Path(SAVE_DIR) / f"{bender.name}.json"
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        print(f"Oyuncunuz '{bender.name}' kaydedildi: {file_path}")
    except Exception as e:
        print(f"'{bender.name}' kaydedilirken hata oluştu: {e}")


def load_game(bender_name): # Bu fonksiyon data.py'deki load_bender_data ile çok benzer
                            # Tutarlılık için bir tanesi tercih edilmeli.
                            # bending_style işlemesi düzeltildi.
    file_path = Path(SAVE_DIR) / f"{bender_name}.json"
    if not file_path.exists():
        print(f"Kayıtlı karakter bulunamadı: {bender_name}")
        return None
        
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            data = json.load(f)

            element_str = data["element"]
            element = Element[element_str.upper()] # Önce Element enum'ını alalım
            
            bending_style_name_from_save = data.get("bending_style") 
            
            style_arg_for_constructor = None
            if bending_style_name_from_save:
                # element.name burada Element enum üyesinin adını (örn: "FIRE") verir.
                element_suffix = "_" + element.name 
                if bending_style_name_from_save.endswith(element_suffix):
                    style_arg_for_constructor = bending_style_name_from_save[:-len(element_suffix)].lower()
                else:
                    # Eğer _ELEMENT soneki yoksa, stil adı daha basit olabilir veya farklı bir formatta kaydedilmiş olabilir.
                    # Örn: "FLIGHT" (FLIGHT_AIR için). Bender.__init__ bunu ("flight", "AIR") ile çözebilir.
                    style_arg_for_constructor = bending_style_name_from_save.lower()
                    if '_' in bending_style_name_from_save and not bending_style_name_from_save.endswith(element_suffix):
                         print(f"Uyarı: Yüklenen stil '{bending_style_name_from_save}' (element: {element.name}) beklenen element sonekini içermiyor ama yine de işleniyor: {style_arg_for_constructor}")


            # Bükücü türüne göre doğru sınıfı çağır
            bender = None
            if element == Element.WATER:
                bender = WaterBender(data["name"], style_arg_for_constructor)
            elif element == Element.FIRE:
                bender = FireBender(data["name"], style_arg_for_constructor)
            elif element == Element.EARTH:
                bender = EarthBender(data["name"], style_arg_for_constructor)
            elif element == Element.AIR:
                bender = AirBender(data["name"], style_arg_for_constructor)
            elif element == Element.ENERGY:
                bender = EnergyBender(data["name"]) 
            else:
                raise ValueError(f"Bilinmeyen element tipi: {element_str}") # Hata fırlat
            
            bender.level = data.get("level",1)
            bender.experience = data.get("experience",0)
            bender.gold = data.get("gold",100)
            bender.reputation = data.get("reputation",0)
            bender.train_count = data.get("train_count", 0) 
            bender.stat_points = data.get("stat_points", 0)

            # Bender.__init__ içinde base_statlar ayarlanır.
            # Kaydedilmiş base_statları yüklemek, seviye atlama bonuslarının doğru hesaplanması için önemlidir.
            bender.base_max_health = data.get("base_max_health", bender.base_max_health)
            bender.base_power = data.get("base_power", bender.base_power)
            bender.base_max_energy = data.get("base_max_energy", bender.base_max_energy)

            # Yetenekleri Ability objeleri olarak yeniden oluştur
            bender.abilities = [] # Önce sıfırla, sonra yükle
            bender.active_abilities = []
            bender.passive_abilities = []
            raw_abilities_data = data.get("abilities", [])
            if raw_abilities_data and isinstance(raw_abilities_data[0], dict):
                for ability_data in raw_abilities_data:
                    ability = Ability(
                        ability_data["name"], ability_data["description"],
                        ability_data["effect_type"], ability_data["effect_amount"],
                        ability_data["energy_cost"], 
                        ability_data.get("is_active", True), # Varsayılan
                        ability_data.get("cooldown", 0),
                        ability_data.get("current_cooldown", 0), # Kaydedilmişse yükle
                        ability_data.get("target_type", "opponent") # Varsayılan
                    )
                    # learn_ability ile eklemek yerine direkt listelere atayalım, çünkü bu kayıtlı durum.
                    bender.abilities.append(ability)
                    if ability.is_active:
                        bender.active_abilities.append(ability)
                    else:
                        bender.passive_abilities.append(ability)
            
            # Envanter ve Ekipmanları Item/Equipment objeleri olarak yeniden oluştur
            bender.inventory = []
            for item_data in data.get("inventory",[]):
                rarity_name = item_data.get("rarity", "COMMON") # to_dict rarity.name kaydeder
                actual_rarity = ItemRarity[rarity_name] if hasattr(ItemRarity, rarity_name) else ItemRarity.COMMON
                
                if item_data.get("slot"): 
                    item = Equipment(item_data["name"], item_data["description"], 
                                    item_data["effect_type"], item_data["effect_amount"], 
                                    item_data["slot"], item_data.get("price",0), 
                                    actual_rarity, 
                                    item_data.get("durability", 100))
                else:
                    item = Item(item_data["name"], item_data["description"], 
                                item_data["effect_type"], item_data["effect_amount"], 
                                item_data.get("price",0), item_data.get("usage_limit", 1),
                                actual_rarity)
                bender.inventory.append(item)
            
            bender.equipped_items = []
            for eq_data in data.get("equipped_items",[]):
                rarity_name = eq_data.get("rarity", "COMMON")
                actual_rarity = ItemRarity[rarity_name] if hasattr(ItemRarity, rarity_name) else ItemRarity.COMMON
                eq = Equipment(eq_data["name"], eq_data["description"], 
                                eq_data["effect_type"], eq_data["effect_amount"], 
                                eq_data["slot"], eq_data.get("price",0), 
                                actual_rarity,
                                eq_data.get("durability", 100))
                bender.equipped_items.append(eq) # Sadece listeye ekle
            
            # Tüm statları, ekipmanları ve pasif yetenekleri hesaba katarak güncelle
            bender.update_stats_from_equipment()

            # Kaydedilmiş anlık can, enerji ve diğer anlık statları yükle (update_stats'tan sonra)
            bender.health = data.get("health", bender.max_health)
            bender.energy = data.get("energy", bender.max_energy)
            # Kaydedilmiş crit_chance ve dodge_chance, update_stats_from_equipment tarafından
            # seviye ve ekipmanlara göre ayarlanır. Eğer buff/debuff ile anlık değişmişse
            # ve bu anlık değerler de kaydedilmişse, onlar burada yüklenebilir.
            # Şimdilik update_stats'ın hesapladığı değerlere güveniyoruz.
            # bender.crit_chance = data.get("crit_chance", bender.crit_chance) 
            # bender.dodge_chance = data.get("dodge_chance", bender.dodge_chance)

            bender.buffs = data.get("buffs", {})
            bender.debuffs = data.get("debuffs", {})
            # Yükleme sonrası bu buff/debuff'ların etkilerini yeniden uygulamak gerekebilir.
            # En güvenlisi, bu buff/debuff'ların etkilerini update_stats_from_equipment içinde hesaba katmaktır.
            # Ya da burada geçici olarak statları tekrar ayarlamaktır. Şimdilik tick_buffs_debuffs'e bırakalım.

            # Özel yetenekler
            bender.special_abilities_unlocked = [BendingStyle[s_name] for s_name in data.get("special_abilities_unlocked", []) if hasattr(BendingStyle, s_name)]

            print(f"Oyuncu '{bender.name}' yüklendi ({file_path}).")
            return bender
            
    except FileNotFoundError:
        print(f"Kayıt dosyası bulunamadı: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Kayıt dosyası ({file_path}) bozuk veya geçersiz JSON formatında.")
        return None
    except Exception as e:
        print(f"Oyunu yüklerken bir hata oluştu ({bender_name}): {e}")
        import traceback
        traceback.print_exc()
        return None

# Quest Sınıfı Tanımı (Güncellenmiş)
class Quest:
    def __init__(self, name, description, requirements, xp_reward, gold_reward, item_reward=None, is_repeatable=False, quest_type="general"):
        self.name = name
        self.description = description
        self.requirements = requirements 
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.item_reward = item_reward # Bu bir Item/Equipment nesnesi olmalı
        self.is_completed = False 
        self.is_repeatable = is_repeatable
        self.quest_type = quest_type 
        self.current_progress = {} 

        for req_type, req_val in self.requirements.items():
            if req_type in ["train_count"]:
                self.current_progress[req_type] = 0
            elif req_type == "enemies_to_defeat": # req_val: {"Orman Canavarı": 3}
                self.current_progress[req_type] = {enemy: 0 for enemy in req_val}
            elif req_type == "item_required": # req_val: [{"name": "Demir Cevheri", "count": 5}]
                self.current_progress[req_type] = {item_data["name"]: 0 for item_data in req_val}


    def update_progress(self, progress_type, value=1, enemy_name=None, item_name=None):
        if self.is_completed and not self.is_repeatable: return # Tamamlanmış ve tekrarlanamazsa ilerleme yok

        if progress_type == "train_count" and "train_count" in self.current_progress:
            self.current_progress["train_count"] = min(self.current_progress.get("train_count",0) + value, self.requirements["train_count"])
        elif progress_type == "enemy_defeated" and enemy_name and "enemies_to_defeat" in self.current_progress:
            if enemy_name in self.current_progress["enemies_to_defeat"]:
                 self.current_progress["enemies_to_defeat"][enemy_name] = min(
                     self.current_progress["enemies_to_defeat"].get(enemy_name,0) + value,
                     self.requirements["enemies_to_defeat"][enemy_name]
                 )
        elif progress_type == "item_collected" and item_name and "item_required" in self.current_progress:
            # item_name, Item nesnesi değil, adı olacak
            for req_item_data in self.requirements.get("item_required", []):
                if req_item_data["name"] == item_name:
                    self.current_progress["item_required"][item_name] = min(
                        self.current_progress["item_required"].get(item_name,0) + value,
                        req_item_data["count"]
                    )
                    break

    def check_requirements(self, bender):
        if self.is_completed and not self.is_repeatable:
            return False # Zaten tamamlanmış ve tekrarlanamaz

        for req_type, req_val in self.requirements.items():
            if req_type == "level" and bender.level < req_val:
                return False
            if req_type == "reputation" and bender.reputation < req_val:
                return False
            if req_type == "train_count": # current_progress'ten kontrol et
                 if self.current_progress.get("train_count", 0) < req_val:
                    return False
            if req_type == "enemies_to_defeat": # current_progress'ten kontrol et
                for enemy, count in req_val.items():
                    if self.current_progress.get("enemies_to_defeat", {}).get(enemy, 0) < count:
                        return False
            if req_type == "item_required": # current_progress'ten kontrol et
                for item_data in req_val: 
                    item_name = item_data["name"]
                    item_count = item_data["count"]
                    # Envanterdeki eşya sayısını kontrol et (görev tesliminde) veya current_progress (toplama görevlerinde)
                    # Bu check_requirements daha çok "görevi alabilir mi?" veya "ilerleme tamamlandı mı?" için.
                    # Teslimat görevleri için envanter kontrolü complete_quest'te yapılabilir.
                    # Toplama görevleri için current_progress'e bakılır.
                    if self.quest_type == "collection":
                        if self.current_progress.get("item_required", {}).get(item_name, 0) < item_count:
                            return False
                    elif self.quest_type == "delivery": # Teslimat için envanterde var mı diye bak
                        found_in_inventory = sum(1 for inv_item in bender.inventory if inv_item.name == item_name)
                        if found_in_inventory < item_count:
                            return False
        return True

    def complete_quest(self, bender):
        if self.check_requirements(bender):
            print(f"\n✅ GÖREV TAMAMLANDI: {self.name}! ✅")
            bender.experience += self.xp_reward
            bender.gold += self.gold_reward
            # bender._check_level_up() # XP artışı sonrası zaten çağrılacak

            if self.item_reward:
                # Item'ı kopyalayarak envantere ekle (özellikle Equipment için önemli)
                # item_reward'ın bir Item veya Equipment nesnesi olduğunu varsayıyoruz.
                reward_item_instance = None
                if isinstance(self.item_reward, Equipment):
                    reward_item_instance = Equipment(
                        self.item_reward.name, self.item_reward.description, 
                        self.item_reward.effect_type, self.item_reward.effect_amount, 
                        self.item_reward.slot, self.item_reward.price, 
                        self.item_reward.rarity, self.item_reward.max_durability # max_durability'den üret
                    )
                elif isinstance(self.item_reward, Item):
                     reward_item_instance = Item(
                        self.item_reward.name, self.item_reward.description, 
                        self.item_reward.effect_type, self.item_reward.effect_amount, 
                        self.item_reward.price, self.item_reward.usage_limit, 
                        self.item_reward.rarity
                    )
                
                if reward_item_instance:
                    bender.add_to_inventory(reward_item_instance)
                    print(f"Ödül: {self.xp_reward} XP, {self.gold_reward} altın ve {reward_item_instance.name}!")
                else: # Sadece XP ve Altın
                    print(f"Ödül: {self.xp_reward} XP ve {self.gold_reward} altın!")
            else:
                print(f"Ödül: {self.xp_reward} XP ve {self.gold_reward} altın!")
            
            bender._check_level_up() # Ödüller sonrası seviye kontrolü

            # Görev gereksinimlerindeki eşyaları envanterden kaldır (eğer teslimat göreviyse)
            if "item_required" in self.requirements and self.quest_type == "delivery":
                for req_item_data in self.requirements["item_required"]:
                    item_name_to_remove = req_item_data["name"]
                    count_to_remove = req_item_data["count"]
                    removed_count = 0
                    items_to_remove_from_inv_list = [] # Önce çıkarılacakları topla
                    for inv_item in bender.inventory:
                        if inv_item.name == item_name_to_remove and removed_count < count_to_remove:
                            items_to_remove_from_inv_list.append(inv_item)
                            removed_count += 1
                    
                    for item_obj_to_del in items_to_remove_from_inv_list:
                        bender.remove_from_inventory(item_obj_to_del)
                    if removed_count > 0:
                        print(f"{removed_count} adet {item_name_to_remove} envanterinizden görev için teslim edildi.")

            if not self.is_repeatable:
                self.is_completed = True
            
            # Her halükarda (tekrarlanabilir veya değil) ilerlemeyi sıfırla ki tekrar alınabilsin/yapılabilsin
            for req_type_key in self.current_progress:
                if isinstance(self.current_progress[req_type_key], dict):
                    for k in self.current_progress[req_type_key]:
                        self.current_progress[req_type_key][k] = 0
                else:
                    self.current_progress[req_type_key] = 0
            
            if self.is_repeatable:
                print(f"💡 {self.name} görevi tekrar tamamlanabilir.")
            return True
        else:
            print(f"❌ {self.name} görevi henüz tamamlanmadı veya gereksinimler karşılanmadı.")
            # print("Gereksinimler:", self.requirements)
            # print("Mevcut İlerleme:", self.current_progress)
            return False

class StoryManager:
    STORY_CHAPTERS = [
        {"title": "Başlangıç 🥚", "description": "Bükme yolculuğunuza başlıyorsunuz.", "requirements": {"level": 1, "reputation": 0}},
        {"title": "İlk Sınav 🥋", "description": "İlk bükme sınavınıza giriyorsunuz. En az seviye 2 olmalısın!", "requirements": {"level": 2, "reputation": 10}}, # İtibar eklendi
        {"title": "Element Ustası 🌟", "description": "Elementinizde ustalaşıyorsunuz. Seviye 5 ve itibar 50 olmalı!", "requirements": {"level": 5, "reputation": 50}},
        {"title": "Turnuva 🏆", "description": "Element turnuvasına katılıyorsunuz. Seviye 7 ve itibar 100 olmalı!", "requirements": {"level": 7, "reputation": 100}},
        {"title": "Usta Bükücü 👑", "description": "Artık bir usta olarak görülüyorsunuz. Seviye 10 ve itibar 200 olmalı!", "requirements": {"level": 10, "reputation": 200}},
        {"title": "Efsanevi Savaş 🐉", "description": "Efsanevi bir savaşa katılıyorsunuz. Seviye 15 ve itibar 300 olmalı!", "requirements": {"level": 15, "reputation": 300}},
        {"title": "Avatar'ın Gölgesi 🌌", "description": "Yeni ve gizemli bir tehdit. Seviye 20 ve itibar 400 olmalı!", "requirements": {"level": 20, "reputation": 400}}
    ]
    
    def __init__(self):
        self.progress = load_story_progress() # game.py içindeki global fonksiyonu kullanır
    
    def update_progress(self, bender): # Bender nesnesi alır
        bender_name = bender.name
        if bender_name not in self.progress:
            self.progress[bender_name] = {"current_chapter_index": 0, "completed_chapter_indices": []}
        
        # current_chapter_index oyuncunun şu anki aktif görevi değil, ulaştığı son bölümü gösterir.
        # Bir sonraki bölüme geçip geçemeyeceğini kontrol ederiz.
        current_reached_chapter_idx = self.progress[bender_name].get("current_chapter_index", 0)
        
        # Henüz tamamlanmamış ve gereksinimleri karşılanan bir sonraki bölüm var mı?
        for i in range(current_reached_chapter_idx, len(self.STORY_CHAPTERS)):
            if i not in self.progress[bender_name]["completed_chapter_indices"]: # Eğer bu bölüm daha önce tamamlanmadıysa
                chapter_info = self.STORY_CHAPTERS[i]
                requirements_met = True
                for req_type, req_val in chapter_info["requirements"].items():
                    if req_type == "level" and bender.level < req_val:
                        requirements_met = False
                        break
                    if req_type == "reputation" and bender.reputation < req_val:
                        requirements_met = False
                        break
                
                if requirements_met:
                    self.progress[bender_name]["completed_chapter_indices"].append(i)
                    self.progress[bender_name]["current_chapter_index"] = i # Ulaşılan son bölümü güncelle
                    save_story_progress(self.progress) # game.py içindeki global fonksiyon
                    print(f"\n⭐ Hikayede ilerledin! '{chapter_info['title']}' bölümü tamamlandı! ⭐")
                    # Bir sonraki bölümün kilidini aç (eğer varsa)
                    if i + 1 < len(self.STORY_CHAPTERS):
                         print(f"Yeni bölüm açıldı: '{self.STORY_CHAPTERS[i+1]['title']}'")
                    return True # Bir ilerleme oldu
        return False # Yeni bir bölüm tamamlanmadı
    
    def get_current_story_display(self, bender_name): # Mevcut aktif bölümü veya bir sonrakini gösterir
        if bender_name not in self.progress:
            # İlk bölümü hedef olarak göster
            return f"Sıradaki: {self.STORY_CHAPTERS[0]['title']} - {self.STORY_CHAPTERS[0]['description']}"

        last_completed_idx = -1
        if self.progress[bender_name]["completed_chapter_indices"]:
            last_completed_idx = max(self.progress[bender_name]["completed_chapter_indices"])

        next_chapter_idx = last_completed_idx + 1
        if next_chapter_idx < len(self.STORY_CHAPTERS):
            next_chap = self.STORY_CHAPTERS[next_chapter_idx]
            req_parts = []
            if "level" in next_chap["requirements"]: req_parts.append(f"Lv {next_chap['requirements']['level']}")
            if "reputation" in next_chap["requirements"]: req_parts.append(f"İtibar {next_chap['requirements']['reputation']}")
            req_str = f" (Gereksinim: {', '.join(req_parts)})" if req_parts else ""
            return f"Sıradaki Hikaye Bölümü: {next_chap['title']} - {next_chap['description']}{req_str}"
        else:
            return "Tebrikler! Tüm hikaye bölümlerini tamamladınız!"

    def show_story_progress(self, bender_name): # Bender'ın adını alır
        print("\n=== Hikaye İlerlemesi 📚 ===")
        if bender_name not in self.progress:
            print("Bu karakter için kayıtlı hikaye ilerlemesi yok.")
            # İlk bölümü göster
            if self.STORY_CHAPTERS:
                print(f"→ 1. {self.STORY_CHAPTERS[0]['title']} - {self.STORY_CHAPTERS[0]['description']}")
            return

        completed_indices = self.progress[bender_name].get("completed_chapter_indices", [])
        
        for i, chapter in enumerate(self.STORY_CHAPTERS):
            status_emoji = " "
            if i in completed_indices:
                status_emoji = "✓" # Tamamlandı
            elif not completed_indices or i == max(completed_indices, default=-1) + 1 : # Bir sonraki aktif bölüm
                status_emoji = "→" # Aktif hedef
            
            req_str_parts = []
            if "level" in chapter["requirements"]: req_str_parts.append(f"Lv {chapter['requirements']['level']}")
            if "reputation" in chapter["requirements"]: req_str_parts.append(f"İtibar {chapter['requirements']['reputation']}")
            req_display = f" (Gereksinim: {', '.join(req_str_parts)})" if req_str_parts else ""

            print(f"{status_emoji} {i+1}. {chapter['title']} - {chapter['description']}{req_display}")
        print(f"\n{self.get_current_story_display(bender_name)}")


# Yeni Map ve Location sınıfları
class Location:
    def __init__(self, name, description, enemies=None, resources=None, special_events=None, min_level=0): # min_level eklendi
        self.name = name
        self.description = description
        self.enemies = enemies if enemies else [] 
        self.resources = resources if resources else [] 
        self.special_events = special_events if special_events else [] 
        self.min_level = min_level # Bu konuma girmek için minimum seviye

class Map: # game_map olarak bir örneği globalde oluşturulabilir.
    def __init__(self):
        self.locations = {
            "Başlangıç Köyü": Location("Başlangıç Köyü", "Maceralarınıza başladığınız huzurlu bir köy.", 
                                       resources=[{"name": "Odun", "chance": 0.6, "min": 1, "max": 2}, {"name": "Ot", "chance": 0.4, "min": 1, "max": 3}]),
            "Vahşi Orman": Location("Vahşi Orman", "Tehlikeli hayvanların ve nadir bitkilerin yaşadığı bir orman.", 
                                    enemies=[("Orman Canavarı", Element.EARTH), ("Vahşi Kurt", Element.FIRE)], # (isim, element türü)
                                    resources=[{"name": "Şifalı Bitki", "chance": 0.7, "min": 1, "max": 3}, {"name": "Nadir Odun", "chance": 0.3, "min": 1, "max": 2}],
                                    special_events=["Gizli Tapınak", "Gizemli Yaratık"], min_level=3),
            "Kaya Geçidi": Location("Kaya Geçidi", "Dağlara açılan zorlu bir geçit.",
                                    enemies=[("Dağ Trolü", Element.EARTH), ("Kaya Golemi", Element.EARTH)],
                                    resources=[{"name": "Demir Cevheri", "chance": 0.5, "min": 1, "max": 2}, {"name": "Değerli Taş", "chance": 0.2, "min": 1, "max": 1}], min_level=5),
            "Donmuş Tundra": Location("Donmuş Tundra", "Sert rüzgarların estiği, buzla kaplı geniş bir arazi.",
                                    enemies=[("Buz Tilkisi", Element.WATER), ("Kutup Ayısı", Element.WATER)],
                                    resources=[{"name": "Buz Kristali", "chance": 0.6, "min": 1, "max": 2}, {"name": "Kutup Otu", "chance": 0.3, "min": 1, "max": 3}],
                                    special_events=["Buz Zindanı"], min_level=7),
            "Kızgın Çöl": Location("Kızgın Çöl", "Güneşin kavurduğu engin kumlar.",
                                    enemies=[("Çöl Akrebi", Element.FIRE), ("Alev Ruhu", Element.FIRE)],
                                    resources=[{"name": "Kumtaşı", "chance": 0.7, "min": 1, "max": 3}, {"name": "Ateş Çiçeği", "chance": 0.3, "min": 1, "max": 1}],
                                    special_events=["Kayıp Harabeler"], min_level=7),
            "Hava Tapınağı Kalıntıları": Location("Hava Tapınağı Kalıntıları", "Kadim bir hava tapınağının kalıntıları.",
                                    enemies=[("Hava Ruhları", Element.AIR)],
                                    resources=[{"name": "Rüzgar Tüyü", "chance": 0.8, "min": 1, "max": 2}],
                                    special_events=["Meditasyon Alanı", "Uçuş Denemesi"], min_level=10),
        }
        self.current_location_name = "Başlangıç Köyü" # Oyuncu burada başlar

    def get_current_location(self):
        return self.locations[self.current_location_name]

    def move_to(self, location_name, player_level):
        if location_name in self.locations:
            target_loc = self.locations[location_name]
            if player_level >= target_loc.min_level:
                self.current_location_name = location_name
                print(f"📍 {target_loc.name} konumuna hareket ettiniz: {target_loc.description}")
                return True
            else:
                print(f"❌ {target_loc.name} konumuna gitmek için çok düşüksünüz. Minimum seviye: {target_loc.min_level}")
                return False
        else:
            print("❌ Böyle bir konum bulunamadı.")
            return False

# Global harita nesnesi
game_map = Map()


# Quest'lerin listesi
QUESTS = [
    Quest("Eğitim Başlangıcı", "Eğitim alanında 3 kez antrenman yap.", {"train_count": 3, "level": 1}, 50, 20, is_repeatable=False),
    Quest("Acemi Bükücü Sınavı", "Rastgele bir rakibi yen (Savaş menüsünden).", {"level": 2}, 100, 50, 
          item_reward=Item("Şifa İksiri", "Küçük bir can iksiri", "health", 30, 0, usage_limit=1, rarity=ItemRarity.COMMON), is_repeatable=False, quest_type="combat"), # Fiyat 0, ödül
    Quest("Gelişim Yolculuğu", "Seviye 5'e ulaş ve 50 itibar kazan.", {"level": 5, "reputation": 50}, 200, 100, 
          item_reward=Item("Güç Takviyesi İksiri", "Geçici güç artışı sağlar.", "power", 10, 0, usage_limit=1, rarity=ItemRarity.UNCOMMON), is_repeatable=False),
    Quest("Günlük Antrenman", "Bugün 5 kez antrenman yap.", {"train_count": 5}, 30, 10, is_repeatable=True), # Tekrarlanabilir
    Quest("Orman Temizliği", "Vahşi Orman'da 3 adet Orman Canavarı yen.", {"enemies_to_defeat": {"Orman Canavarı": 3}, "level": 3}, 150, 75, 
          item_reward=Item("Orman Büyüsü İksiri", "Geçici XP artışı sağlar.", "xp", 50, 0, usage_limit=1, rarity=ItemRarity.COMMON), is_repeatable=True, quest_type="combat"),
    Quest("Maden Toplama", "Kaya Geçidi'nden 5 adet Demir Cevheri topla (Keşfet menüsünden).", {"item_required": [{"name": "Demir Cevheri", "count": 5}], "level": 5}, 120, 60, 
          item_reward=Item("Maden İksiri", "Enerjiyi yeniler.", "energy", 30, 0, usage_limit=1, rarity=ItemRarity.COMMON), is_repeatable=True, quest_type="collection"),
    Quest("Antik Gizem", "Seviye 10'a ulaş, 150 itibar kazan ve Hava Tapınağı Kalıntıları'nı ziyaret et (Keşfet menüsünden).", {"level": 10, "reputation": 150}, 300, 150, 
          item_reward=Equipment("Kadim Asa", "Gizemli bir asa. (+15 Güç, +10 Maks Enerji)", "power_boost", 15, "weapon", 0, rarity=ItemRarity.RARE, durability=150), is_repeatable=False), # Fiyat 0, ödül
    Quest("Gölge Avcısı", "Zindanda 'Gölge Canavarı'nı yen (Zindan Keşfi).", {"enemies_to_defeat": {"Gölge Canavarı": 1}, "level": 8}, 250, 120, 
          item_reward=Equipment("Gölge Zırhı", "Sinsi ve hafif zırh. (+20 Maks Can, +0.03 Kaçınma Şansı)", "health_boost", 20, "armor", 0, rarity=ItemRarity.RARE, durability=120), is_repeatable=False, quest_type="combat"),
    Quest("Kıymetli Taş Teslimatı", "Başlangıç Köyü'nden Kaya Geçidi'ndeki Tüccar'a 1 adet Değerli Taş teslim et (Keşfet ile topla, sonra bu görevi tamamla).", {"item_required": [{"name": "Değerli Taş", "count": 1}], "level": 6}, 180, 90, is_repeatable=False, quest_type="delivery"),
]


# SHOP_ITEMS ve EQUIPMENT_ITEMS (Genişletilmiş)
# Fiyatlar güncellendi, nadirlik eklendi
SHOP_ITEMS = [
    Item("Küçük Şifa İksiri", "Anında 30 can yeniler.", "health", 30, 20, usage_limit=1, rarity=ItemRarity.COMMON),
    Item("Büyük Şifa İksiri", "Anında 80 can yeniler.", "health", 80, 50, usage_limit=1, rarity=ItemRarity.UNCOMMON),
    Item("Küçük Enerji İksiri", "Anında 25 enerji yeniler.", "energy", 25, 25, usage_limit=1, rarity=ItemRarity.COMMON),
    Item("Büyük Enerji İksiri", "Anında 60 enerji yeniler.", "energy", 60, 55, usage_limit=1, rarity=ItemRarity.UNCOMMON),
    # Item("Güç Takviyesi", "Geçici olarak 15 güç artırır.", "power", 15, 30, usage_limit=1, rarity=ItemRarity.COMMON), # Bu bir buff olmalı, bender.apply_buff ile
    Item("Deneyim Parşömeni (Küçük)", "50 deneyim kazandırır.", "xp", 50, 70, usage_limit=1, rarity=ItemRarity.COMMON),
    Item("Deneyim Parşömeni (Büyük)", "150 deneyim kazandırır.", "xp", 150, 180, usage_limit=1, rarity=ItemRarity.UNCOMMON),
    Item("İtibar Nişanı", "20 itibar kazandırır.", "reputation", 20, 100, usage_limit=1, rarity=ItemRarity.UNCOMMON),
    # Item("Kritik Odaklanma İksiri", "Geçici olarak kritik vuruş şansını %10 artırır.", "crit_chance", 0.10, 70, usage_limit=1, rarity=ItemRarity.RARE), # Bu da buff
    # Item("Hızlı Ayak İksiri", "Geçici olarak kaçınma şansını %10 artırır.", "dodge_chance", 0.10, 70, usage_limit=1, rarity=ItemRarity.RARE), # Bu da buff

    # Yetenek Kitapları
    Item("Yetenek Kitabı: Gelgit Dalgası (Su)", "Su bükücüler için: Güçlü bir alan etkili saldırı.", "ability", "Gelgit Dalgası", 250, usage_limit=1, rarity=ItemRarity.RARE), 
    Item("Yetenek Kitabı: Mavi Alev (Ateş)", "Ateş bükücüler için: Yüksek hasarlı tek hedef saldırı.", "ability", "Mavi Alev", 300, usage_limit=1, rarity=ItemRarity.RARE),
    Item("Yetenek Kitabı: Lav Bükme (Toprak)", "Toprak bükücüler için: Alan etkili hasar yeteneği.", "ability", "Lav Bükme", 280, usage_limit=1, rarity=ItemRarity.RARE), 
    Item("Yetenek Kitabı: Uçma (Hava)", "Hava bükücüler için: Pasif kaçınma yeteneği.", "ability", "Uçma", 270, usage_limit=1, rarity=ItemRarity.RARE),
    Item("Yetenek Kitabı: Kritik Gelişim", "Kalıcı olarak kritik vuruş şansını artırır (Pasif).", "ability", "Kritik Vuruş Gelişimi", 500, usage_limit=1, rarity=ItemRarity.EPIC),
    Item("Yetenek Kitabı: Enerji Emilimi", "Saldırıdan enerji çalma şansı kazandırır (Pasif).", "ability", "Enerji Absorpsiyonu", 450, usage_limit=1, rarity=ItemRarity.EPIC),
]

EQUIPMENT_ITEMS = [
    # Silahlar
    Equipment("Tahta Asa", "Basit bir antrenman asası. (+5 Güç)", "power_boost", 5, "weapon", 50, rarity=ItemRarity.COMMON, durability=70),
    Equipment("Demir Kılıç", "Sağlam bir demir kılıç. (+10 Güç)", "power_boost", 10, "weapon", 120, rarity=ItemRarity.UNCOMMON, durability=90),
    Equipment("Kristal Asa", "Enerji akışını hızlandıran bir asa. (+8 Güç, +10 Maks Enerji)", "power_boost", 8, "weapon", 250, rarity=ItemRarity.RARE, durability=110), # Güç biraz dengelendi
    Equipment("Efsanevi Kılıç", "Efsanevi bir savaşçının kılıcı. (+20 Güç, +0.03 Kritik Şans)", "power_boost", 20, "weapon", 700, rarity=ItemRarity.EPIC, durability=150), # Güç biraz dengelendi
    Equipment("Avatar'ın Asası", "Avatar'ın gücüyle dolu. (+30 Güç, +15 Maks Enerji, +0.05 Kritik Şans, +0.05 Kaçınma Şansı)", "power_boost", 30, "weapon", 1500, rarity=ItemRarity.LEGENDARY, durability=200),

    # Zırhlar
    Equipment("Deri Zırh", "Hafif ve esnek deri zırh. (+15 Maks Can)", "health_boost", 15, "armor", 80, rarity=ItemRarity.COMMON, durability=80),
    Equipment("Plaka Zırh", "Ağır ve dayanıklı plaka zırh. (+30 Maks Can)", "health_boost", 30, "armor", 180, rarity=ItemRarity.UNCOMMON, durability=120), # Güç azaltma kaldırıldı, basitlik için
    Equipment("Element Zırhı", "Elementinize uyum sağlayan özel zırh. (+25 Maks Can, +10 Maks Enerji)", "health_boost", 25, "armor", 350, rarity=ItemRarity.RARE, durability=140),
    Equipment("Ejderha Derisi Zırh", "Nadir bir ejderhanın derisinden yapılmış. (+40 Maks Can, +0.02 Kritik Şans)", "health_boost", 40, "armor", 800, rarity=ItemRarity.EPIC, durability=180),
    Equipment("Mistik Zırh", "Antik bükücülerin büyülü zırhı. (+50 Maks Can, +15 Maks Enerji, +0.03 Kaçınma Şansı)", "health_boost", 50, "armor", 1600, rarity=ItemRarity.LEGENDARY, durability=220),

    # Aksesuarlar (Kolyeler, Yüzükler) - Tek bir "accessory" slotu var gibi düşünülüyor
    Equipment("Bronz Kolye", "Basit bir kolye. (+5 Maks Can)", "health_boost", 5, "accessory", 30, rarity=ItemRarity.COMMON, durability=50),
    Equipment("Gümüş Yüzük", "Şifa özellikli bir yüzük. (+8 Maks Can)", "health_boost", 8, "accessory", 60, rarity=ItemRarity.UNCOMMON, durability=60),
    Equipment("Enerji Yüzüğü", "Enerji akışını artıran yüzük. (+10 Maks Enerji)", "energy_boost", 10, "accessory", 90, rarity=ItemRarity.RARE, durability=70),
    Equipment("Koruyucu Muska", "Savunmayı güçlendirir. (+12 Maks Can, +0.01 Kaçınma Şansı)", "health_boost", 12, "accessory", 150, rarity=ItemRarity.RARE, durability=80),
    Equipment("Efsanevi Yüzük", "Gizemli güçlere sahip. (+5 Güç, +5 Maks Can, +5 Maks Enerji)", "power_boost", 5, "accessory", 500, rarity=ItemRarity.EPIC, durability=100), # Etkileri dengeli

    # Yeni slotlar: Ayakkabılar, Eldivenler
    Equipment("Basit Botlar", "Yürüyüş için rahat. (+3 Maks Can)", "health_boost", 3, "boots", 40, rarity=ItemRarity.COMMON, durability=60),
    Equipment("Çevik Botlar", "Daha hızlı hareket etmenizi sağlar. (+0.02 Kaçınma Şansı)", "dodge_chance_boost", 0.02, "boots", 80, rarity=ItemRarity.UNCOMMON, durability=70),
    Equipment("Savaşçı Eldivenleri", "Daha sağlam yumruklar. (+3 Güç)", "power_boost", 3, "gloves", 50, rarity=ItemRarity.COMMON, durability=60),
    Equipment("Bükme Eldivenleri", "Bükme hassasiyetini artırır. (+5 Güç, +5 Maks Enerji)", "power_boost", 5, "gloves", 110, rarity=ItemRarity.RARE, durability=80),
]

# Hammaddeler (Crafting için)
CRAFTING_RESOURCES = [ # Bunlar Item nesneleri olmalı ve effect_type="resource" olmalı
    Item("Odun", "Basit bir ahşap parçası.", "resource", 0, 2, usage_limit=0, rarity=ItemRarity.COMMON), # Fiyat eklendi (satın alınabilir diye)
    Item("Ot", "Yeşil, sıradan bir ot.", "resource", 0, 1, usage_limit=0, rarity=ItemRarity.COMMON),
    Item("Şifalı Bitki", "İksir yapımında kullanılır.", "resource", 0, 5, usage_limit=0, rarity=ItemRarity.COMMON),
    Item("Demir Cevheri", "Demir eritmek için kullanılır.", "resource", 0, 10, usage_limit=0, rarity=ItemRarity.UNCOMMON),
    Item("Değerli Taş", "Nadiren bulunur, değerli eşyalarda kullanılır.", "resource", 0, 50, usage_limit=0, rarity=ItemRarity.RARE),
    Item("Buz Kristali", "Buz ve su bükme yeteneklerinde kullanılır.", "resource", 0, 15, usage_limit=0, rarity=ItemRarity.UNCOMMON),
    Item("Kutup Otu", "Dondurucu iksirlerde kullanılır.", "resource", 0, 8, usage_limit=0, rarity=ItemRarity.COMMON),
    Item("Kumtaşı", "Toprak bükmede kullanılır.", "resource", 0, 4, usage_limit=0, rarity=ItemRarity.COMMON),
    Item("Ateş Çiçeği", "Ateş bükmede ve ateş iksirlerinde kullanılır.", "resource", 0, 12, usage_limit=0, rarity=ItemRarity.UNCOMMON),
    Item("Rüzgar Tüyü", "Hava bükmede ve hız iksirlerinde kullanılır.", "resource", 0, 10, usage_limit=0, rarity=ItemRarity.UNCOMMON),
    Item("Deri Parçası", "Zırh ve giysi yapımında kullanılır.", "resource", 0, 7, usage_limit=0, rarity=ItemRarity.COMMON), # Deri eklendi
]


# Crafting Tarifleri
# Çıktılar da Item/Equipment nesneleri olmalı
CRAFTING_RECIPES = {
    "Küçük Şifa İksiri": {
        "materials": {"Şifalı Bitki": 2, "Ot": 1}, # Su yerine Ot (daha kolay bulunur)
        "output": Item("Küçük Şifa İksiri", "Anında 30 can yeniler.", "health", 30, 20, usage_limit=1, rarity=ItemRarity.COMMON)
    },
    "Tahta Asa": {
        "materials": {"Odun": 3}, 
        "output": Equipment("Tahta Asa", "Basit bir antrenman asası. (+5 Güç)", "power_boost", 5, "weapon", 50, rarity=ItemRarity.COMMON, durability=70)
    },
    "Demir Kılıç": { # Daha fazla malzeme isteyebilir
        "materials": {"Demir Cevheri": 2, "Odun": 1, "Deri Parçası": 1}, 
        "output": Equipment("Demir Kılıç", "Sağlam bir demir kılıç. (+10 Güç)", "power_boost", 10, "weapon", 120, rarity=ItemRarity.UNCOMMON, durability=90)
    },
    "Basit Botlar": {
        "materials": {"Deri Parçası": 2, "Ot": 1}, # Odun yerine Ot
        "output": Equipment("Basit Botlar", "Yürüyüş için rahat. (+3 Maks Can)", "health_boost", 3, "boots", 40, rarity=ItemRarity.COMMON, durability=60)
    },
    "Küçük Enerji İksiri": {
        "materials": {"Kutup Otu": 1, "Rüzgar Tüyü": 1}, # Daha az malzeme
        "output": Item("Küçük Enerji İksiri", "Anında 25 enerji yeniler.", "energy", 25, 25, usage_limit=1, rarity=ItemRarity.COMMON)
    },
    "Deri Zırh": {
        "materials": {"Deri Parçası": 5, "Ot": 2},
        "output": Equipment("Deri Zırh", "Hafif ve esnek deri zırh. (+15 Maks Can)", "health_boost", 15, "armor", 80, rarity=ItemRarity.COMMON, durability=80)
    }
}


def get_element_emoji(element_enum): # Element enum üyesi alır
    if element_enum == Element.WATER: return "🌊"
    if element_enum == Element.FIRE: return "🔥"
    if element_enum == Element.EARTH: return "⛰️"
    if element_enum == Element.AIR: return "💨"
    if element_enum == Element.ENERGY: return "⚛️"
    return ""

def choose_player_character(benders_list, prompt="Bir karakter seçin:"): # benders_list olarak adlandıralım
    if not benders_list:
        print("Kayıtlı veya aktif karakter bulunamadı.") # Mesaj güncellendi
        return None
    
    print(f"\n=== {prompt} 🧙 ===")
    for i, bender_obj in enumerate(benders_list, 1): # bender_obj olarak adlandıralım
        print(f"{i}. {bender_obj.name} - Seviye {bender_obj.level} {bender_obj.element.name.capitalize()} Bükücüsü {get_element_emoji(bender_obj.element)}")
    print("0. Geri")

    try:
        choice_input = input("Seçiminiz: ")
        if not choice_input.isdigit(): # Sayı değilse kontrol et
            print("❌ Geçersiz giriş! Lütfen bir sayı girin.")
            return None # None döndür, böylece çağıran yer kontrol edebilir
        
        choice_idx = int(choice_input) - 1 # choice_idx olarak adlandıralım
        if choice_idx == -1: # 0 girilirse (Geri)
            return None
        if 0 <= choice_idx < len(benders_list):
            return benders_list[choice_idx]
        else:
            print("❌ Geçersiz seçim!")
            return None
    except ValueError: # int'e çevirme hatası için
        print("❌ Geçersiz giriş! Lütfen bir sayı girin.")
        return None

def create_character_interactive():
    print("\n=== Yeni Karakter Oluştur 🧙 ===")
    name = input("Karakter adı: ").strip()
    if not name:
        print("❌ Karakter adı boş olamaz.")
        return None
    
    print("\nElement seçin:")
    elements_list = list(Element) # Enum üyelerini liste olarak al
    for i, el_enum in enumerate(elements_list, 1):
        print(f"{i}. {el_enum.name.capitalize()} {get_element_emoji(el_enum)}")
    
    element_str = ""
    try:
        element_choice_input = input(f"Seçiminiz (1-{len(elements_list)}): ")
        if not element_choice_input.isdigit():
            print("❌ Geçersiz element seçimi!")
            return None
        element_choice_idx = int(element_choice_input) - 1
        if 0 <= element_choice_idx < len(elements_list):
            element_str = elements_list[element_choice_idx].name # Enum adını al (örn: "WATER")
        else:
            print("❌ Geçersiz element seçimi!")
            return None
        
        bending_style_str_arg = None # choose_bender'a gidecek argüman
        # Element stili seçimi
        if element_str == "WATER":
            print("\nSu Bükme Stili:")
            print("1. Northern (Kuzey Su: Dengeli)")
            print("2. Southern (Güney Su: Şifa odaklı)")
            style_choice = input("Seçiminiz (1-2, boş bırakırsanız varsayılan stil olmaz): ").strip()
            if style_choice == "1": bending_style_str_arg = "northern"
            elif style_choice == "2": bending_style_str_arg = "southern"
        elif element_str == "FIRE":
            print("\nAteş Bükme Stili:")
            print("1. Sun_Warrior (Güneş Savaşçısı: Geleneksel)") # Enum ile uyumlu olması için alt tireli
            print("2. Rouge (Asi Ateş: Daha agresif, riskli)")
            style_choice = input("Seçiminiz (1-2): ").strip()
            if style_choice == "1": bending_style_str_arg = "sun_warrior" 
            elif style_choice == "2": bending_style_str_arg = "rouge"
        elif element_str == "EARTH":
            print("\nToprak Bükme Stili:")
            print("1. Earth_Rumble (Temel Toprak: Dayanıklı)")
            print("2. Sand_Bending (Kum Bükme: Çevik, kontrol odaklı)")
            style_choice = input("Seçiminiz (1-2): ").strip()
            if style_choice == "1": bending_style_str_arg = "earth_rumble"
            elif style_choice == "2": bending_style_str_arg = "sand_bending"
        elif element_str == "AIR":
            print("\nHava Bükme Stili:")
            print("1. Air_Nomad (Hava Göçebesi: Denge ve kaçınma)")
            print("2. Flight (Uçuş: Daha hızlı, kaçınma odaklı)")
            style_choice = input("Seçiminiz (1-2): ").strip()
            if style_choice == "1": bending_style_str_arg = "air_nomad"
            elif style_choice == "2": bending_style_str_arg = "flight"
        
        # choose_bender element string'ini (örn: "WATER") ve stil string'ini (örn: "northern") alır
        new_bender = choose_bender(name, element_str.lower(), bending_style_str_arg) 
        
        if new_bender:
            print(f"\n🎉 {name} başarıyla oluşturuldu! ({new_bender.element.name.capitalize()} bükücüsü {get_element_emoji(new_bender.element)}) 🎉")
            if new_bender.bending_style:
                print(f"Bükme Stili: {new_bender.bending_style.name.replace('_', ' ').title()}")
            return new_bender
        else: # choose_bender None dönerse (beklenmedik bir durum)
            print("❌ Karakter oluşturulamadı.")
            return None
            
    except ValueError: # int'e çevirme hatası vb.
        print("❌ Geçersiz giriş yapıldı!")
        return None
    except KeyError as e: # Geçersiz enum adı için
        print(f"❌ Geçersiz stil veya element adı hatası: {e}")
        return None


def show_status(bender):
    print(f"\n=== {bender.name} Durumu 👤 ===")
    print(f"Element: {bender.element.name.capitalize()} {get_element_emoji(bender.element)}")
    if bender.bending_style:
        print(f"Bükme Stili: {bender.bending_style.name.replace('_', ' ').title()}")
    print(f"Seviye: {bender.level} ✨ (Sonraki için: {bender.experience}/{100 * bender.level} XP)")
    print(f"Güç: {int(bender.power)} 💪") # int ile gösterim
    print(f"Can: {int(bender.health)}/{int(bender.max_health)} ❤️")
    print(f"Enerji: {int(bender.energy)}/{int(bender.max_energy)} ⚡")
    print(f"Altın: {bender.gold} 💰")
    print(f"İtibar: {bender.reputation} 👑")
    print(f"Antrenman Sayısı: {bender.train_count} 🏋️")
    if bender.stat_points > 0:
        print(f"Dağıtılmamış Stat Puanları: {bender.stat_points} 🔼")
    print(f"Kritik Şans: {bender.crit_chance*100:.1f}% 💥") # Yüzde olarak göster
    print(f"Kaçınma Şansı: {bender.dodge_chance*100:.1f}% 💨") # Yüzde olarak göster
    
    print("\nAktif Yetenekler 🤸 (Savaşta Kullanılabilir):")
    if bender.active_abilities:
        for i, ability in enumerate(bender.active_abilities, 1):
            cooldown_info = f"(CD: {ability.cooldown}, Kalan: {ability.current_cooldown})" if ability.cooldown > 0 else ""
            print(f"  {i}. {ability.name} - Enerji: {ability.energy_cost} {cooldown_info} ({ability.description})")
    else:
        print("  Aktif yeteneği yok.")

    print("\nPasif Yetenekler 🧘 (Sürekli Etkili):")
    if bender.passive_abilities:
        for i, ability in enumerate(bender.passive_abilities, 1):
            print(f"  {i}. {ability.name} ({ability.description})")
    else:
        print("  Pasif yeteneği yok.")


    if bender.special_abilities_unlocked:
        print("\nÖzel Yetenek Stilleri (Bükme Stili ile Açılanlar) ✨:")
        for style_enum in bender.special_abilities_unlocked:
            print(f"- {style_enum.name.replace('_', ' ').title()}")
    
    if bender.equipped_items:
        print("\nKuşanılmış Ekipmanlar 🛡️:")
        for eq in bender.equipped_items:
            print(f"- [{eq.slot.capitalize()}] {eq.name} (D: {eq.durability}/{eq.max_durability}) - {eq.description} [{eq.rarity.value}]")
    else:
        print("\nKuşanılmış ekipman yok.")

    if bender.inventory:
        print("\nEnvanter 🎒:")
        # Eşyaları sayarak göstermek daha iyi olabilir
        item_counts = {}
        for item_obj in bender.inventory: # item_obj olarak adlandıralım
            # Anahtar olarak (isim, açıklama, nadirlik) gibi bir tuple kullanılabilir
            # Ancak aynı isimde farklı özelliklerde eşyalar olabilir (örn: farklı durability)
            # Şimdilik sadece isimle sayalım, detaylı gösterimde tüm özellikler görünür.
            item_key = item_obj.name 
            if item_key not in item_counts:
                item_counts[item_key] = {"item_ref": item_obj, "count": 0}
            item_counts[item_key]["count"] += 1

        for key_name, data in item_counts.items():
            item_ref = data["item_ref"] # Referans olarak ilk bulunanı alalım
            count = data["count"]
            rarity_str = f" [{item_ref.rarity.value}]"
            durability_str = f" (D: {item_ref.durability}/{item_ref.max_durability})" if isinstance(item_ref, Equipment) else ""
            usage_str = ""
            if isinstance(item_ref, Item) and not isinstance(item_ref, Equipment) and item_ref.effect_type != "resource":
                 usage_str = f" (Kullanım: {'Sınırsız' if item_ref.usage_limit == 0 else item_ref.usage_limit})"
            
            print(f"- {item_ref.name} x{count}{rarity_str}: {item_ref.description}{usage_str}{durability_str}")
    else:
        print("\nEnvanter boş.")
    
    # Hikaye ilerlemesi için StoryManager kullanılır, burada direkt gösterilmez.
    # print("\nHikaye İlerlemesi 📖:")
    # story_mngr = StoryManager() # Her seferinde yeni oluşturmak yerine global bir tane kullanılabilir.
    # print(story_mngr.get_current_story_display(bender.name))


def distribute_stat_points(bender):
    if bender.stat_points <= 0:
        print("❌ Dağıtacak stat puanınız yok.")
        return

    print(f"\n=== Stat Puanı Dağıtımı ({bender.stat_points} Puan Mevcut) ===")
    print(f"Mevcut Değerler: Maks Can: {int(bender.max_health)}, Güç: {int(bender.power)}, Maks Enerji: {int(bender.max_energy)}")
    print("1. Maksimum Can (+1 puan = +5 Maks Can)")
    print("2. Güç (+1 puan = +2 Güç)")
    print("3. Maksimum Enerji (+1 puan = +3 Maks Enerji)")
    print("0. Bitir ve Geri Dön")

    while bender.stat_points > 0:
        try:
            choice = input(f"Puan vermek istediğiniz stat (Kalan Puan: {bender.stat_points}): ").strip()
            if choice == "0":
                break
            if choice not in ["1", "2", "3"]:
                print("❌ Geçersiz stat seçimi. Lütfen 1, 2, 3 veya 0 girin.")
                continue

            points_to_spend_str = input("Bu stata kaç puan vermek istersiniz?: ").strip()
            if not points_to_spend_str.isdigit():
                print("❌ Geçersiz puan miktarı. Lütfen bir sayı girin.")
                continue
            
            points_to_spend = int(points_to_spend_str)
            if points_to_spend <= 0:
                print("❌ En az 1 puan vermelisiniz.")
                continue
            if points_to_spend > bender.stat_points:
                print(f"❌ Yeterli stat puanınız yok. En fazla {bender.stat_points} puan verebilirsiniz.")
                continue

            if choice == "1": # Maks Can
                # Stat puanları base değerleri artırmalı, sonra update_stats_from_equipment çağrılmalı
                bender.base_max_health += (points_to_spend * 5)
                print(f"❤️ Baz Maksimum canınız {points_to_spend * 5} arttı.")
            elif choice == "2": # Güç
                bender.base_power += (points_to_spend * 2)
                print(f"💪 Baz Gücünüz {points_to_spend * 2} arttı.")
            elif choice == "3": # Maks Enerji
                bender.base_max_energy += (points_to_spend * 3)
                print(f"⚡ Baz Maksimum enerjiniz {points_to_spend * 3} arttı.")
            
            bender.stat_points -= points_to_spend
            bender.update_stats_from_equipment() # Değişiklikleri yansıt
            # Anlık can ve enerjiyi de artırılan maksimuma göre ayarla (eğer max arttıysa)
            bender.health = min(bender.health + (points_to_spend * 5 if choice == "1" else 0), bender.max_health)
            bender.energy = min(bender.energy + (points_to_spend * 3 if choice == "3" else 0), bender.max_energy)

            print(f"Yeni Değerler: Maks Can: {int(bender.max_health)}, Güç: {int(bender.power)}, Maks Enerji: {int(bender.max_energy)}")
            if bender.stat_points == 0:
                print("Tüm stat puanları dağıtıldı.")
                break
        except ValueError:
            print("❌ Geçersiz giriş! Lütfen bir sayı girin.")
        except Exception as e: # Genel hata yakalama
            print(f"Stat dağıtımı sırasında bir hata oluştu: {e}")
    
    bender.update_stats_from_equipment() # Son bir kez güncelle
    print("Stat puanı dağıtımı tamamlandı.")


def train_character_action(bender): # Bender nesnesi alır
    print(f"\n{bender.name} eğitime başlıyor... 🏋️")
    
    print("\nEğitim Türü:")
    print("1. Temel Bükme Antrenmanı (Genel XP, rastgele küçük stat artışı)")
    print("2. Element Odaklı Meditasyon (Daha fazla XP, Güç veya Enerji artışı)")
    print("3. Dövüş Talimi (Az XP, yeni basit bir saldırı yeteneği öğrenme şansı)")
    print("0. Geri")
    
    training_type = input("Seçiminiz (0-3): ").strip()
    
    xp_kazanci = 0
    if training_type == "1":
        xp_kazanci = bender.train() # train() zaten XP verir ve _check_level_up çağırır
        # Rastgele küçük stat artışı
        stat_choice = random.choice(["health", "power", "energy"])
        if stat_choice == "health": bender.base_max_health += random.randint(1,3); print("Baz maks. can biraz arttı.")
        elif stat_choice == "power": bender.base_power += 1; print("Baz güç biraz arttı.")
        else: bender.base_max_energy += random.randint(1,2); print("Baz maks. enerji biraz arttı.")
        bender.update_stats_from_equipment()
        print(f"💪 {bender.name} temel antrenman yaptı ve {xp_kazanci} XP kazandı!")
    elif training_type == "2":
        xp_kazanci = bender.train() + 10 # Ekstra XP
        bender.experience += 10 # Manuel ekle, train zaten ekledi
        if random.random() < 0.5:
            bonus_power = random.randint(1, 2)
            bender.base_power += bonus_power
            print(f"Meditasyon baz gücünü {bonus_power} artırdı.")
        else:
            bonus_energy = random.randint(2, 4)
            bender.base_max_energy += bonus_energy
            print(f"Meditasyon baz maks. enerjini {bonus_energy} artırdı.")
        bender.update_stats_from_equipment()
        bender._check_level_up() # XP eklendiği için kontrol
        print(f"✨ {bender.name} element meditasyonu yaptı, toplam {xp_kazanci} XP kazandı!")
    elif training_type == "3":
        xp_kazanci = bender.train() // 2 # Daha az XP
        bender.experience -= xp_kazanci # train() tam ekledi, yarısını geri alalım
        
        # Yeni bir yetenek öğrenme şansı (basit bir saldırı yeteneği)
        if random.random() < 0.25 + (bender.reputation * 0.0005): # %25 + itibara göre artan şans
            # Elementine uygun basit bir saldırı yeteneği
            new_basic_ability = None
            if bender.element == Element.WATER and "Su Jeti" not in [a.name for a in bender.abilities]:
                new_basic_ability = Ability("Su Jeti", "Odaklanmış bir su saldırısı.", "damage", bender.power * 0.6, 4, cooldown=1)
            elif bender.element == Element.FIRE and "Kıvılcım" not in [a.name for a in bender.abilities]:
                new_basic_ability = Ability("Kıvılcım", "Hızlı bir ateş püskürtmesi.", "damage", bender.power * 0.5, 3, cooldown=1)
            elif bender.element == Element.EARTH and "Çakıl Taşı Yağmuru" not in [a.name for a in bender.abilities]:
                new_basic_ability = Ability("Çakıl Taşı Yağmuru", "Küçük ama çok sayıda taş fırlatır.", "damage", bender.power * 0.7, 5, cooldown=1)
            elif bender.element == Element.AIR and "Hafif Esinti" not in [a.name for a in bender.abilities]:
                 new_basic_ability = Ability("Hafif Esinti Saldırısı", "Keskin bir hava akımı gönderir.", "damage", bender.power * 0.5, 3, cooldown=1)

            if new_basic_ability:
                bender.learn_ability(new_basic_ability) # learn_ability mesaj basar
            else:
                 print(f"😔 {bender.name} dövüş talimi yaptı ama yeni bir saldırı tekniği öğrenemedi.")
        else:
            print(f"😔 {bender.name} dövüş talimi yaptı ama yeni bir saldırı tekniği öğrenemedi.")
        bender._check_level_up() # XP değiştiği için kontrol
        print(f"✨ Dövüş taliminden {xp_kazanci} XP kazandı!")
    elif training_type == "0":
        print("Antrenman yapmadan geri dönülüyor.")
        return # Fonksiyondan çık
    else:
        print("❌ Geçersiz antrenman seçimi.")
        return

    # Hikaye ilerlemesini her antrenman sonrası kontrol et (StoryManager global olmalı veya paslanmalı)
    # story_mngr = StoryManager() # Her seferinde oluşturmak yerine global kullan
    # story_mngr.update_progress(bender)
    
    # Görev kontrolü (QUESTS global olmalı veya paslanmalı)
    for quest in QUESTS:
        if not quest.is_completed or quest.is_repeatable: # Tamamlanmamış veya tekrarlanabilir görevler için
            if "train_count" in quest.requirements:
                quest.update_progress("train_count", 1) 
                # check_requirements ve complete_quest manage_quests menüsünde yapılabilir.
                # Otomatik tamamlanma isteniyorsa:
                # if quest.check_requirements(bender):
                #    quest.complete_quest(bender)


def battle_arena(player, opponent): # Bender nesneleri alır
    print(f"\n⚔️ SAVAŞ ARENASI: {player.name} vs {opponent.name} ⚔️")
    # player.battle(opponent) zaten detaylı log basıyor.
    result = player.battle(opponent) # Bu "win", "lose", "ran_away", "draw" döndürür
    
    # Hikaye ilerlemesi (StoryManager global olmalı)
    # story_mngr = StoryManager()
    # story_mngr.update_progress(player) 
    
    return result # Savaş sonucunu döndür


def visit_elemental_temple(bender_obj): # Bender nesnesi alır
    print("\n⛩️ Kadim Element Tapınağı ⛩️")
    print(f"{bender_obj.name}, {bender_obj.element.name.capitalize()} elementinin tapınağına adım attı.")
    print("Hava elementin saf gücüyle titreşiyor...")

    time.sleep(1)
    event_chance = random.randint(1, 100)

    if event_chance <= 35: # %35
        print("Antik bir sunak keşfettin. Elementine olan bağın derinleşti.")
        bonus_xp = random.randint(20, 40) + bender_obj.level * 2
        bender_obj.experience += bonus_xp
        print(f"{bonus_xp} XP kazandın!")
        if random.random() < 0.2: # %20 şansla stat puanı
            bender_obj.stat_points += 1
            print("Ekstra 1 Stat Puanı kazandın!")
        bender_obj._check_level_up()
    elif event_chance <= 65: # %30 (36-65)
        print("Eski yazıtlar okudun ve elementinin unutulmuş bir tekniğini hatırladın.")
        # Elementine özel basit bir pasif veya aktif yetenek öğrenme şansı
        # Bu kısım daha detaylı yetenek havuzları gerektirir. Şimdilik basit bir mesaj.
        print("Yeni bir anlayış kazandın (oyun mekaniği olarak etki eklenebilir).")
        bender_obj.reputation += 5
        print("5 İtibar kazandın.")
    elif event_chance <= 85: # %20 (66-85)
        print("Tapınakta meditasyon yaparken ruhun dinlendi.")
        heal_perc = random.uniform(0.25, 0.50) # %25-%50 arası can yenile
        energy_perc = random.uniform(0.30, 0.60) # %30-%60 arası enerji yenile
        bender_obj.heal(bender_obj.max_health * heal_perc)
        bender_obj.energy = min(bender_obj.max_energy, bender_obj.energy + bender_obj.max_energy * energy_perc)
        print(f"Can ve enerjinin bir kısmı yenilendi.")
    else: # %15 (86-100)
        print("Tapınağın koruyucu ruhu sana küçük bir hediye sundu.")
        gift_choices = [
            Item("Saf Enerji Kristali", "Nadir bir enerji kaynağı.", "resource", 0, 100, usage_limit=0, rarity=ItemRarity.RARE),
            Item("Tapınak Tılsımı", "Şans getirdiğine inanılır.", "gold", random.randint(50,150), 0, usage_limit=1, rarity=ItemRarity.UNCOMMON) # Altın veren bir eşya
        ]
        chosen_gift = random.choice(gift_choices)
        if chosen_gift.effect_type == "gold": # Eğer altın veren bir eşyaysa direkt altın verelim
            bender_obj.gold += chosen_gift.effect_amount
            print(f"'{chosen_gift.name}' buldun ve {chosen_gift.effect_amount} altın kazandın!")
        else:
            bender_obj.add_to_inventory(chosen_gift)
            # print(f"'{chosen_gift.name}' envanterine eklendi.") # add_to_inventory zaten mesaj basıyor

    print("Element Tapınağı'ndan ayrıldın.")
    print("-------------------------------------------\n")

def initiate_battle(benders_list): # Ana oyuncu listesini alır
    global game_map # Düşman seçimi için harita bilgisi kullanılabilir
    print("\n=== Savaş Seçenekleri ⚔️ ===")
    print("1. Rastgele Bilgisayar Rakibine Karşı Savaş (Arenada)")
    print("2. Kendi Karakterlerimden Birine Karşı Savaş (Dostluk Maçı)")
    # print("3. Element Turnuvası (Hikayede ilerleyince açılır)") # Şimdilik kapalı
    print("0. Geri")

    battle_choice = input("Seçiminiz: ").strip()
    if battle_choice == "0":
        return

    player = choose_player_character(benders_list, "Savaşacak karakteri seçin:")
    if not player:
        return # Karakter seçilmedi
    
    # Savaş öncesi can ve enerjiyi kaydet (özellikle dostluk maçı için)
    player_original_health = player.health 
    player_original_energy = player.energy

    opponent = None
    if battle_choice == "1":
        elements_for_opponent = list(Element) # Tüm elementlerden biri
        opponent_element = random.choice(elements_for_opponent)
        
        # Rakip bükücü için rastgele bir stil seçimi (eğer varsa)
        opponent_style_str = None
        possible_styles_for_element = []
        if opponent_element == Element.WATER: possible_styles_for_element = ["northern", "southern"]
        elif opponent_element == Element.FIRE: possible_styles_for_element = ["sun_warrior", "rouge"]
        elif opponent_element == Element.EARTH: possible_styles_for_element = ["earth_rumble", "sand_bending"]
        elif opponent_element == Element.AIR: possible_styles_for_element = ["air_nomad", "flight"]
        if possible_styles_for_element:
            opponent_style_str = random.choice(possible_styles_for_element)

        opponent = choose_bender(f"Arena Rakibi {random.randint(100, 999)}", opponent_element.name.lower(), opponent_style_str)
        
        # Rakibin seviyesini ve statlarını oyuncuya göre ayarla
        opponent.level = max(1, player.level + random.randint(-1, 2)) # Oyuncudan -1 ile +2 seviye arası
        # Rakibin temel statlarını kendi seviyesine göre ayarla (Bender.__init__ yapar)
        # Sonra biraz rastgelelik ekle
        opponent.base_power += random.randint(-3, 3)
        opponent.base_max_health += random.randint(-10, 10)
        opponent.update_stats_from_equipment() # Ekipmansız halini güncelle
        
        # Rakibe rastgele birkaç temel yetenek ekle (kendi _get_initial_abilities zaten ekliyor)
        # Daha fazla yetenek eklenebilir.
        
        print(f"\nRakip: {opponent.name} (Seviye {opponent.level}, {get_element_emoji(opponent.element)} {opponent.element.name.capitalize()})")
        battle_result = battle_arena(player, opponent) # player.battle çağırır
        
        # Görev kontrolü (Savaş sonrası)
        if battle_result == "win":
            for q in QUESTS:
                if not q.is_completed or q.is_repeatable:
                    if q.name == "Acemi Bükücü Sınavı" and q.check_requirements(player):
                        q.complete_quest(player)
                    # Daha genel "düşman yen" görevleri için:
                    if "enemies_to_defeat" in q.requirements:
                        # Rakibin adı veya türü görevle eşleşiyor mu kontrol et
                        # Şimdilik genel bir "rakip yenildi" olarak kabul edelim.
                        # q.update_progress("enemy_defeated", 1, enemy_name="Arena Rakibi") # Örnek
                        pass # Bu kısım daha detaylı eşleştirme gerektirir.

    elif battle_choice == "2":
        if len(benders_list) < 2:
            print("❌ Kendi karakterlerinize karşı savaşmak için en az iki karakteriniz olmalı.")
            player.health = player_original_health # Canı geri yükle
            player.energy = player_original_energy
            return

        available_opponents = [b for b in benders_list if b != player]
        if not available_opponents:
            print("❌ Savaşacak başka kayıtlı karakteriniz yok.")
            player.health = player_original_health
            player.energy = player_original_energy
            return

        print("Kime karşı dostluk maçı yapmak istersiniz?")
        opponent = choose_player_character(available_opponents, "Rakip karakteri seçin:")
        if not opponent:
            player.health = player_original_health # Seçim iptal edilirse canı geri yükle
            player.energy = player_original_energy
            return
        
        opponent_original_health = opponent.health 
        opponent_original_energy = opponent.energy

        battle_result = battle_arena(player, opponent) # player.battle çağırır

        # Dostluk maçı sonrası can ve enerjileri geri yükle
        player.health = player_original_health 
        player.energy = player_original_energy
        opponent.health = opponent_original_health
        opponent.energy = opponent_original_energy
        print("\nCanlarınız ve enerjileriniz dostluk maçı öncesi durumuna geri döndü.")

    # elif battle_choice == "3": # Turnuva mantığı buraya eklenebilir
    #     story_mngr = StoryManager()
    #     # Gerekli hikaye bölümüne ulaşılmış mı kontrol et
    #     # ... turnuva kodu ...
    #     pass

    else:
        print("❌ Geçersiz savaş seçimi.")
        # Oyuncunun canını geri yükle (eğer bir işlem yapılmadıysa)
        player.health = player_original_health
        player.energy = player_original_energy
    
    # Her savaş sonrası (eğer oyuncu bir işlem yaptıysa) biraz şehir olayı şansı
    # if opponent: # Eğer bir savaş gerçekleştiyse
    #    if random.random() < 0.15: # %15 şans
    #        random_city_event(player)


def shop_menu(bender): # Bender nesnesi alır
    print("\n=== Dükkan 🏪 ===")
    print(f"Altın: {bender.gold} 💰")
    
    discount_rate = 0
    if bender.reputation >= 200: discount_rate = 0.15; print("🎉 Yüksek itibarınız sayesinde %15 indirim kazandınız!")
    elif bender.reputation >= 100: discount_rate = 0.05; print("🥳 İtibarınız sayesinde %5 indirim kazandınız!")

    # Satılacak eşyaları birleştir (SHOP_ITEMS + EQUIPMENT_ITEMS)
    # Nadirliğe ve sonra fiyata göre sırala
    available_for_sale = sorted(
        [item for item in SHOP_ITEMS + EQUIPMENT_ITEMS], 
        key=lambda x: (list(ItemRarity).index(x.rarity), x.price) # Önce nadirlik, sonra fiyat
    )
    
    print("\n--- Satın Alınabilir Eşyalar ---")
    for i, item_to_sell in enumerate(available_for_sale, 1):
        display_price = int(item_to_sell.price * (1 - discount_rate))
        
        rarity_str = f" [{item_to_sell.rarity.value}]"
        item_display = f"{i}. {item_to_sell.name}{rarity_str} - Fiyat: {display_price} 💰 ({item_to_sell.description})"

        if isinstance(item_to_sell, Equipment):
            item_display += f" (Slot: {item_to_sell.slot.capitalize()})"
        elif item_to_sell.effect_type == "ability":
            # Yetenek kitapları için uygunluk kontrolü
            can_learn = True
            # Element kontrolü (kitap adına göre basit kontrol)
            if "Su Bükme" in item_to_sell.name and bender.element != Element.WATER: can_learn = False
            elif "Ateş Bükme" in item_to_sell.name and bender.element != Element.FIRE: can_learn = False
            elif "Toprak Bükme" in item_to_sell.name and bender.element != Element.EARTH: can_learn = False
            elif "Hava Bükme" in item_to_sell.name and bender.element != Element.AIR: can_learn = False
            # Genel yetenek kitapları (element adı içermeyenler) için bu kontrol atlanır.

            if not can_learn:
                item_display += " (Elementinize uygun değil)"
            elif item_to_sell.effect_amount in [ab.name for ab in bender.abilities]: 
                item_display += " (Zaten Sahipsiniz)"
            
        print(item_display)
    
    print("0. Geri")

    try:
        choice_input = input("Satın almak istediğiniz ürün numarası: ").strip()
        if not choice_input.isdigit():
            print("❌ Geçersiz giriş!")
            return
        
        choice_idx = int(choice_input) -1 
        if choice_idx == -1: # 0. Geri
            return
        
        if 0 <= choice_idx < len(available_for_sale):
            selected_item_blueprint = available_for_sale[choice_idx] # Bu bir şablon
            actual_price = int(selected_item_blueprint.price * (1 - discount_rate))

            can_buy_and_learn = True # Yetenek kitapları için ek kontrol
            if selected_item_blueprint.effect_type == "ability":
                if "Su Bükme" in selected_item_blueprint.name and bender.element != Element.WATER: can_buy_and_learn = False
                elif "Ateş Bükme" in selected_item_blueprint.name and bender.element != Element.FIRE: can_buy_and_learn = False
                elif "Toprak Bükme" in selected_item_blueprint.name and bender.element != Element.EARTH: can_buy_and_learn = False
                elif "Hava Bükme" in selected_item_blueprint.name and bender.element != Element.AIR: can_buy_and_learn = False
                
                if not can_buy_and_learn:
                    print("❌ Bu yetenek kitabı elementinize uygun değil.")
                elif selected_item_blueprint.effect_amount in [ab.name for ab in bender.abilities]:
                    print(f"❌ '{selected_item_blueprint.effect_amount}' yeteneğine zaten sahipsiniz.")
                    can_buy_and_learn = False

            if not can_buy_and_learn: # Eğer öğrenilemiyorsa satın alma
                return

            if bender.gold >= actual_price:
                bender.gold -= actual_price
                # Eşyayı kopyalayarak envantere ekle
                newly_bought_item = None
                if isinstance(selected_item_blueprint, Equipment):
                    newly_bought_item = Equipment(selected_item_blueprint.name, selected_item_blueprint.description, 
                                        selected_item_blueprint.effect_type, selected_item_blueprint.effect_amount, 
                                        selected_item_blueprint.slot, selected_item_blueprint.price, # Orijinal fiyatı sakla
                                        selected_item_blueprint.rarity, selected_item_blueprint.max_durability)
                elif isinstance(selected_item_blueprint, Item): # Normal Item (yetenek kitabı dahil)
                    newly_bought_item = Item(selected_item_blueprint.name, selected_item_blueprint.description, 
                                    selected_item_blueprint.effect_type, selected_item_blueprint.effect_amount, 
                                    selected_item_blueprint.price, selected_item_blueprint.usage_limit, 
                                    selected_item_blueprint.rarity)
                
                if newly_bought_item:
                    bender.add_to_inventory(newly_bought_item)
                    # print(f"✅ {newly_bought_item.name} satın aldınız!") # add_to_inventory mesaj basar
                else: # Beklenmedik durum
                    bender.gold += actual_price # Altını geri ver
                    print("Satın alma sırasında bir hata oluştu.")
            else:
                print("❌ Yeterli altınınız yok!")
        else:
            print("❌ Geçersiz ürün seçimi!")
    except ValueError:
        print("❌ Geçersiz giriş! Lütfen bir sayı girin.")


def inventory_menu(bender): # Bender nesnesi alır
    while True: # Envanterden çıkana kadar döngüde kal
        print("\n=== Envanter 🎒 ===")
        if not bender.inventory and not bender.equipped_items:
            print("Envanteriniz boş ve kuşanılmış ekipmanınız yok.")
            print("0. Geri")
            if input("Seçiminiz: ").strip() == "0": return
            continue # Döngünün başına

        display_list = [] # (item_nesnesi, kaynak_türü ["equipped", "inventory_item_ref", "inventory_group_key"])
        
        if bender.equipped_items:
            print("\n--- Kuşanılmış Ekipmanlar 🛡️ ---")
            for eq_item in bender.equipped_items: # eq_item olarak adlandıralım
                display_list.append( (eq_item, "equipped", None) ) # Üçüncü eleman grup anahtarı (yok)
                print(f"{len(display_list)}. [Kuşanılmış] {eq_item.name} (Slot: {eq_item.slot.capitalize()}, D: {eq_item.durability}/{eq_item.max_durability}) [{eq_item.rarity.value}] - {eq_item.description}")
        
        print("\n--- Envanterdeki Eşyalar ---")
        # Eşyaları gruplayarak ve sayarak göster
        inventory_item_groups = {} # item_instance_key -> {"item_ref": item_obj, "objects": [item_obj1, item_obj2]}
        for inv_item_obj in bender.inventory:
            # Aynı isim, açıklama, nadirlik, slot (varsa), max_dayanıklılık (varsa), kullanım limiti (varsa) olanları grupla
            # Bu key, eşyaların "türünü" belirler.
            item_type_key_parts = [
                inv_item_obj.name, inv_item_obj.description, inv_item_obj.rarity.name,
                inv_item_obj.effect_type, str(inv_item_obj.effect_amount) # Sayısal değerleri string'e çevir
            ]
            if isinstance(inv_item_obj, Equipment):
                item_type_key_parts.extend([inv_item_obj.slot, str(inv_item_obj.max_durability)])
            else: # Normal Item
                item_type_key_parts.append(str(inv_item_obj.usage_limit))
            
            item_instance_key = tuple(item_type_key_parts)

            if item_instance_key not in inventory_item_groups:
                inventory_item_groups[item_instance_key] = {"item_ref": inv_item_obj, "objects": []}
            inventory_item_groups[item_instance_key]["objects"].append(inv_item_obj)

        if inventory_item_groups:
            # Grupları nadirliğe ve isme göre sırala
            sorted_group_keys = sorted(inventory_item_groups.keys(), key=lambda k: (
                list(ItemRarity).index(inventory_item_groups[k]["item_ref"].rarity), # Nadirlik sırası
                inventory_item_groups[k]["item_ref"].name # İsim
            ))

            for group_key in sorted_group_keys:
                group_data = inventory_item_groups[group_key]
                item_ref = group_data["item_ref"] # Grubun referans eşyası
                item_obj_list = group_data["objects"] # Bu türdeki tüm eşya nesneleri
                count = len(item_obj_list)

                display_list.append( (item_ref, "inventory_group", item_obj_list) ) # item_obj_list'i de yolla

                rarity_str = f" [{item_ref.rarity.value}]"
                durability_str = f" (D: {item_ref.durability}/{item_ref.max_durability})" if isinstance(item_ref, Equipment) else ""
                usage_str = ""
                if isinstance(item_ref, Item) and not isinstance(item_ref, Equipment) and item_ref.effect_type != "resource":
                    usage_str = f" (K: {'Sınırsız' if item_ref.usage_limit == 0 else item_ref.usage_limit})"
                
                print(f"{len(display_list)}. {item_ref.name} x{count}{rarity_str}: {item_ref.description}{usage_str}{durability_str}")
        else:
            print("  Envanterde başka eşya yok.")
        
        print("0. Geri")

        try:
            choice_input = input("İşlem yapmak istediğiniz eşyanın numarasını girin: ").strip()
            if not choice_input.isdigit(): print("❌ Geçersiz giriş!"); continue
            
            selected_idx = int(choice_input) -1
            if selected_idx == -1: return # 0. Geri

            if 0 <= selected_idx < len(display_list):
                selected_item_tuple = display_list[selected_idx]
                item_object_to_act_on = selected_item_tuple[0] # Referans eşya veya kuşanılmış eşya
                item_source_type = selected_item_tuple[1] # "equipped" veya "inventory_group"
                inventory_group_objects = selected_item_tuple[2] if item_source_type == "inventory_group" else [item_object_to_act_on]
                
                # item_object_to_act_on her zaman listedeki ilk obje veya tek obje olacak
                # Eğer bir gruptan işlem yapılıyorsa, listeden bir tane seçip onunla işlem yapmalıyız.
                # Örneğin, 5 tane Küçük Şifa İksiri varsa, birini kullanırız.
                # Bu yüzden inventory_group_objects listesinden bir tane alırız (genelde ilki).
                actual_item_instance_for_action = inventory_group_objects[0] if inventory_group_objects else None
                if not actual_item_instance_for_action: # Beklenmedik durum
                    print("Eşya bulunamadı!"); continue


                print(f"\nSeçilen: {actual_item_instance_for_action.name}")
                action_options = ["0. Geri"]
                if item_source_type == "equipped": # Kuşanılmış ise
                    action_options.append("1. Çıkar")
                    if isinstance(actual_item_instance_for_action, Equipment) and actual_item_instance_for_action.durability < actual_item_instance_for_action.max_durability:
                        action_options.append(f"2. Tamir Et (Maliyet: {int((actual_item_instance_for_action.max_durability - actual_item_instance_for_action.durability) * 0.5)} Altın)")
                
                elif item_source_type == "inventory_group": # Envanterdeki bir grup ise
                    if isinstance(actual_item_instance_for_action, Equipment):
                        action_options.append("1. Kuşan")
                        if actual_item_instance_for_action.durability < actual_item_instance_for_action.max_durability:
                             action_options.append(f"2. Tamir Et (Maliyet: {int((actual_item_instance_for_action.max_durability - actual_item_instance_for_action.durability) * 0.5)} Altın)")
                    elif actual_item_instance_for_action.effect_type != "resource": # Kaynaklar kullanılamaz
                        action_options.append("1. Kullan")
                    
                    action_options.append("3. Sat (Değer: {int(actual_item_instance_for_action.price * 0.4)} Altın)") # %40'ına satılsın

                print("Ne yapmak istersiniz?")
                for opt in action_options: print(opt)
                
                item_action_choice = input("Seçiminiz: ").strip()

                if item_action_choice == "0": continue # Envanter menüsüne geri dön

                if item_source_type == "equipped":
                    if item_action_choice == "1": # Çıkar
                        if actual_item_instance_for_action.unequip(bender): # bender.equipped_items'tan çıkarır
                            bender.add_to_inventory(actual_item_instance_for_action) # Envantere ekler
                            # print(f"'{actual_item_instance_for_action.name}' çıkarıldı ve envantere eklendi.") # unequip ve add_to_inventory mesaj basar
                    elif item_action_choice == "2" and "Tamir Et" in action_options[-1]: # Tamir
                        repair_cost = int((actual_item_instance_for_action.max_durability - actual_item_instance_for_action.durability) * 0.5)
                        if bender.gold >= repair_cost:
                            bender.gold -= repair_cost
                            actual_item_instance_for_action.repair()
                            # print(f"🛠️ {actual_item_instance_for_action.name} {repair_cost} altına tamir edildi.") # repair metodu mesaj basar
                        else:
                            print(f"❌ Yeterli altınınız yok. Tamir için {repair_cost} altın gerekli.")
                    else: print("❌ Geçersiz işlem.")
                
                elif item_source_type == "inventory_group":
                    if item_action_choice == "1": # Kuşan veya Kullan
                        if isinstance(actual_item_instance_for_action, Equipment):
                            actual_item_instance_for_action.equip(bender) # Envanterden çıkarır, kuşanır
                        elif actual_item_instance_for_action.effect_type != "resource":
                            if actual_item_instance_for_action.use(bender): # Kullanır (ve gerekirse envanterden siler)
                                if actual_item_instance_for_action.usage_limit == 0 and actual_item_instance_for_action.effect_type != "resource": # Eğer kullanım hakkı bittiyse
                                    # use metodu zaten bunu yönetiyorsa (veya yönetmeli), burada tekrar remove çağırmaya gerek yok.
                                    # Ancak emin olmak için:
                                    if actual_item_instance_for_action in bender.inventory: # Hala envanterdeyse (örn: sınırsız kullanım bitmediyse)
                                        pass # Sorun yok
                                    # else: # Kullanım sonrası envanterden silindiyse (tek kullanımlıklar)
                                    # print(f"'{actual_item_instance_for_action.name}' kullanıldı ve tükendi.")
                                    pass # use metodu içindeki remove_from_inventory bunu halletmeli
                            # else: # Kullanım başarısız olduysa use() mesaj basar
                        else: print("Bu eşya kullanılamaz/kuşanılamaz.")
                    
                    elif item_action_choice == "2" and isinstance(actual_item_instance_for_action, Equipment) and "Tamir Et" in action_options[-1 if len(action_options)>2 else 1]: # Envanterdeki ekipmanı tamir
                        repair_cost = int((actual_item_instance_for_action.max_durability - actual_item_instance_for_action.durability) * 0.5)
                        if bender.gold >= repair_cost:
                            bender.gold -= repair_cost
                            actual_item_instance_for_action.repair()
                        else:
                            print(f"❌ Yeterli altınınız yok. Tamir için {repair_cost} altın gerekli.")

                    elif item_action_choice == "3" and "Sat" in action_options[-1]: # Sat
                        sell_price = int(actual_item_instance_for_action.price * 0.4) 
                        confirm_sell = input(f"'{actual_item_instance_for_action.name}' eşyasını {sell_price} altına satmak istiyor musunuz? (E/H): ").strip().lower()
                        if confirm_sell == 'e':
                            if bender.remove_from_inventory(actual_item_instance_for_action): # Gruptan bir tane sil
                                bender.gold += sell_price
                                print(f"✅ {actual_item_instance_for_action.name}, {sell_price} altına satıldı.")
                            # else: # remove_from_inventory mesaj basar
                        else: print("Satış iptal edildi.")
                    else: print("❌ Geçersiz işlem.")
            else:
                print("❌ Geçersiz eşya seçimi!")
        except ValueError:
            print("❌ Geçersiz giriş! Lütfen bir sayı girin.")
        except Exception as e:
            print(f"Envanterde bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()


def manage_quests(bender): # Bender nesnesi alır
    print("\n=== Görevler 📜 ===")
    
    available_quests_to_show = [] # (quest_nesnesi, index_in_QUESTS)
    active_quests_in_progress = []
    completed_quests_done = []

    for i, q_obj in enumerate(QUESTS): # q_obj olarak adlandıralım
        if q_obj.is_repeatable: # Tekrarlanabilir görevler her zaman listelenebilir
            available_quests_to_show.append((q_obj, i))
        elif not q_obj.is_completed: # Tamamlanmamış ve tekrarlanamaz
            available_quests_to_show.append((q_obj, i))
        else: # Tamamlanmış ve tekrarlanamaz
            completed_quests_done.append((q_obj,i))
            
    if not available_quests_to_show and not completed_quests_done:
        print("Hiç görev bulunmuyor.")
        return

    actionable_display_list = [] # Kullanıcının seçebileceği görevler için (quest_obj, original_QUESTS_index)

    if available_quests_to_show:
        print("\n--- Mevcut / Aktif Görevler ---")
        # Görevleri seviye gereksinimine göre sırala
        available_quests_to_show.sort(key=lambda x: x[0].requirements.get("level",0))

        for q_obj, original_idx in available_quests_to_show:
            # Oyuncu görevi alabilir mi / görebilir mi? (Minimum seviye kontrolü)
            if bender.level < q_obj.requirements.get("level", 0):
                # print(f"  (Gizli Görev - Seviye {q_obj.requirements.get('level',0)} gerekir)")
                continue # Şimdilik seviyesi yetmeyenleri gösterme

            actionable_display_list.append((q_obj, original_idx))
            display_idx = len(actionable_display_list) # 1'den başlayan numara

            status_str = ""
            if q_obj.check_requirements(bender): # Tüm gereksinimler tamam mı?
                status_str = "✅ Tamamlanmaya Hazır!"
            else:
                status_str = "⏳ Devam Ediyor..."
            
            repeat_str = "[Tekrarlanabilir]" if q_obj.is_repeatable else "[Tek Seferlik]"
            
            progress_details_list = []
            if "train_count" in q_obj.requirements:
                progress_details_list.append(f"Antrenman: {q_obj.current_progress.get('train_count', 0)}/{q_obj.requirements['train_count']}")
            if "enemies_to_defeat" in q_obj.requirements:
                for enemy, count in q_obj.requirements["enemies_to_defeat"].items():
                    progress_details_list.append(f"{enemy}: {q_obj.current_progress.get('enemies_to_defeat', {}).get(enemy, 0)}/{count}")
            if "item_required" in q_obj.requirements:
                for item_data in q_obj.requirements["item_required"]:
                    item_name = item_data["name"]
                    item_count = item_data["count"]
                    current_val = 0
                    if q_obj.quest_type == "collection": # Toplama ise progress'e bak
                        current_val = q_obj.current_progress.get('item_required', {}).get(item_name, 0)
                    elif q_obj.quest_type == "delivery": # Teslimatsa envantere bak
                        current_val = sum(1 for inv_item in bender.inventory if inv_item.name == item_name)
                    progress_details_list.append(f"{item_name}: {current_val}/{item_count}")

            print(f"{display_idx}. {q_obj.name} {repeat_str} - Durum: {status_str}")
            print(f"   Açıklama: {q_obj.description}")
            if progress_details_list:
                print(f"   İlerleme: {'; '.join(progress_details_list)}")
            print(f"   Ödül: {q_obj.xp_reward} XP, {q_obj.gold_reward} Altın" + (f", {q_obj.item_reward.name}" if q_obj.item_reward else ""))

    if completed_quests_done:
        print("\n--- Tamamlanmış Görevler (Tekrarlanamaz) ---")
        completed_quests_done.sort(key=lambda x: x[0].requirements.get("level",0))
        for q_obj, original_idx in completed_quests_done:
            print(f"- {q_obj.name} (✓ Tamamlandı)")

    if not actionable_display_list:
        print("\nŞu anda tamamlayabileceğiniz veya devam eden uygun bir görev yok.")
        print("0. Geri")
        if input("Seçiminiz: ").strip() == "0": return
        return


    print("0. Geri")
    try:
        choice_input = input("Tamamlamak istediğiniz görevin numarasını girin (veya 0): ").strip()
        if not choice_input.isdigit(): print("❌ Geçersiz giriş!"); return

        selected_display_idx = int(choice_input) -1
        if selected_display_idx == -1: return # 0. Geri
        
        if 0 <= selected_display_idx < len(actionable_display_list):
            quest_to_complete, _ = actionable_display_list[selected_display_idx]
            if quest_to_complete.check_requirements(bender):
                quest_to_complete.complete_quest(bender) # complete_quest mesaj basar
            else:
                print(f"'{quest_to_complete.name}' görevinin gereksinimleri henüz tamamlanmadı.")
        else:
            print("❌ Geçersiz görev seçimi!")
    except ValueError:
        print("❌ Geçersiz giriş! Lütfen bir sayı girin.")


def explore_location(bender, current_game_map: Map): # Bender ve Map nesnesi alır
    current_loc = current_game_map.get_current_location()
    print(f"\n=== {current_loc.name} Keşfediliyor... 🏞️ ===")
    print(current_loc.description)

    while True:
        print("\nNe yapmak istersiniz?")
        print("1. Çevreyi Ara (Kaynak Topla / Özel Etkinlik Bul)")
        print("2. Tehlikelerle Yüzleş (Rastgele Düşmanla Savaş)")
        print("0. Bu konumdan Ayrıl (Ana Menüye Dön)") # Konumdan ayrılma seçeneği

        explore_choice = input("Seçiminiz: ").strip()

        if explore_choice == "0":
            print(f"{current_loc.name} konumundan ayrılıyorsunuz.")
            break # Keşif döngüsünden çık

        elif explore_choice == "1": # Çevreyi Ara
            print("\nÇevreyi dikkatlice arıyorsunuz...")
            time.sleep(0.5)
            found_anything = False

            # Önce özel etkinlik şansı
            if current_loc.special_events and random.random() < 0.20: # %20 özel etkinlik şansı
                found_anything = True
                event_type = random.choice(current_loc.special_events)
                print(f"✨ Özel bir şey fark ettin: {event_type}! ✨")
                # Özel etkinlikleri işleyen bir fonksiyon çağrılabilir
                # handle_special_location_event(bender, event_type, current_loc)
                # Şimdilik basit örnekler:
                if event_type == "Gizli Tapınak":
                    print("Gizemli, antik bir tapınağın girişini buldun!")
                    if input("İçeri girmek ister misin? (E/H): ").strip().lower() == 'e':
                        visit_elemental_temple(bender) # Daha önce tanımlanmış fonksiyonu kullan
                elif event_type == "Gizemli Yaratık":
                    print("Nadiren görülen, gizemli bir yaratıkla karşılaştın!")
                    # Savaş veya hediye senaryosu eklenebilir
                    if random.random() < 0.5:
                        print("Yaratık sana dostça yaklaştı ve küçük bir hediye bıraktı.")
                        gift = Item("Parlayan Taş", "Enerji dolu nadir bir taş.", "resource", 0, 75, rarity=ItemRarity.RARE)
                        bender.add_to_inventory(gift)
                    else:
                        print("Yaratık ürktü ve hızla gözden kayboldu.")
                elif event_type == "Buz Zindanı" and current_loc.name == "Donmuş Tundra":
                    print("Donmuş Tundra'nın derinliklerinde bir Buz Zindanı'nın girişi belirdi!")
                    if input("Zindana girmek ister misin? (E/H): ").strip().lower() == 'e':
                        explore_dungeon(bender) # Zindan keşif fonksiyonu
                # Diğer özel etkinlikler buraya eklenebilir
                # ...
            
            # Kaynak toplama (eğer özel etkinlik olmadıysa veya olsa bile kaynak da bulunabilir)
            if not found_anything or random.random() < 0.7: # %70 şansla kaynak da ara
                resources_found_this_turn = False
                for res_info in current_loc.resources:
                    if random.random() < res_info["chance"]:
                        amount = random.randint(res_info["min"], res_info["max"])
                        # CRAFTING_RESOURCES listesinden doğru Item nesnesini bul
                        resource_item_blueprint = next((r_item for r_item in CRAFTING_RESOURCES if r_item.name == res_info["name"]), None)
                        if resource_item_blueprint:
                            for _ in range(amount): # Her birini ayrı nesne olarak ekle
                                bender.add_to_inventory(Item(
                                    resource_item_blueprint.name, resource_item_blueprint.description,
                                    resource_item_blueprint.effect_type, resource_item_blueprint.effect_amount,
                                    resource_item_blueprint.price, resource_item_blueprint.usage_limit, # usage_limit=0 (sınırsız)
                                    resource_item_blueprint.rarity
                                ))
                            # print(f"✅ {amount} adet {resource_item_blueprint.name} buldunuz!") # add_to_inventory mesaj basar
                            found_anything = True
                            resources_found_this_turn = True
                            # Görev ilerlemesini güncelle (toplama görevleri için)
                            for q in QUESTS:
                                if not q.is_completed or q.is_repeatable:
                                    if q.quest_type == "collection" and "item_required" in q.requirements:
                                        for req_item_d in q.requirements["item_required"]:
                                            if req_item_d["name"] == resource_item_blueprint.name:
                                                q.update_progress("item_collected", amount, item_name=resource_item_blueprint.name)
                                                # Otomatik tamamlama burada yapılabilir veya manage_quests'te kullanıcı tarafından
                                                # if q.check_requirements(bender): q.complete_quest(bender)
                                                break 
                if not resources_found_this_turn and not found_anything: # Eğer özel etkinlik de kaynak da yoksa
                     print("😔 Bu sefer etrafta ilginç bir şey bulamadın.")
                elif resources_found_this_turn and not found_anything: # Sadece kaynak bulunduysa
                     pass # add_to_inventory mesajları yeterli

        elif explore_choice == "2": # Tehlikelerle Yüzleş
            if not current_loc.enemies:
                print("Bu bölgede şu anlık bir tehlike görünmüyor.")
                continue

            print("Dikkat! Bir rakiple karşılaşıyorsun!")
            time.sleep(0.5)
            enemy_name_template, enemy_element = random.choice(current_loc.enemies) # Element de alınıyor
            
            # Düşmanın stilini de rastgele belirleyebiliriz (eğer elementi için stil varsa)
            enemy_style_str = None
            possible_styles = []
            if enemy_element == Element.WATER: possible_styles = ["northern", "southern"]
            elif enemy_element == Element.FIRE: possible_styles = ["sun_warrior", "rouge"]
            # ... diğerleri için de eklenebilir
            if possible_styles: enemy_style_str = random.choice(possible_styles)

            opponent_bender = choose_bender(f"{enemy_name_template} ({current_loc.name})", enemy_element.name.lower(), enemy_style_str)
            
            # Rakibin seviyesini ve statlarını ayarla
            opponent_bender.level = max(1, bender.level + random.randint(current_loc.min_level - bender.level -1, 2)) # Konum min seviyesine yakın
            opponent_bender.base_power += random.randint(-2, bender.level // 3)
            opponent_bender.base_max_health += random.randint(-5, bender.level * 2)
            opponent_bender.update_stats_from_equipment() # Ekipmansız halini güncelle
            
            print(f"Karşına çıkan: {opponent_bender.name} (Seviye {opponent_bender.level}, {get_element_emoji(opponent_bender.element)} {opponent_bender.element.name.capitalize()})!")
            battle_outcome = bender.battle(opponent_bender)

            if battle_outcome == "win":
                print(f"🎉 {opponent_bender.name} yenildi!")
                # Görev ilerlemesini güncelle (düşman yenme görevleri için)
                for q in QUESTS:
                     if not q.is_completed or q.is_repeatable:
                        if q.quest_type == "combat" and "enemies_to_defeat" in q.requirements:
                            if enemy_name_template in q.requirements["enemies_to_defeat"]: # Şablon adıyla eşleşme
                                q.update_progress("enemy_defeated", 1, enemy_name=enemy_name_template)
                                # if q.check_requirements(bender): q.complete_quest(bender)
            elif battle_outcome == "lose":
                print("😔 Savaşı kaybettin. Biraz canın yenilenerek geri çekildin.")
                bender.health = max(1, bender.max_health // 3) # Canın 1/3'ü ile hayatta kal
            # "ran_away" veya "draw" durumlarında özel bir işlem yapmaya gerek yok, battle() mesaj basar.
        
        else:
            print("❌ Geçersiz keşif seçimi.")


def explore_dungeon(bender): # Bender nesnesi alır
    print(f"\n=== {bender.name} Gizemli Bir Zindana Giriyor... 🗝️ ===")
    print("Zindan karanlık ve tehlikelerle dolu. İlerledikçe farklı olaylarla karşılaşabilirsin.")
    
    rooms_explored = 0
    max_rooms_in_dungeon = random.randint(4, 8) # Zindan uzunluğu
    dungeon_level_bonus = bender.level // 2 # Zindan zorluğu oyuncu seviyesine göre artsın
    
    original_health_before_dungeon = bender.health
    original_energy_before_dungeon = bender.energy

    while rooms_explored < max_rooms_in_dungeon:
        rooms_explored += 1
        print(f"\n--- Zindan Odası {rooms_explored}/{max_rooms_in_dungeon} ---")
        time.sleep(0.5)
        event_roll = random.randint(1, 100)

        if bender.health <= 0: # Her oda başında can kontrolü
            print("Zindanda daha fazla ilerleyemeyecek durumdasın.")
            break

        if event_roll <= 45: # %45 Düşman
            print(" menacing bir gölge yaklaşıyor... Bir canavarla karşılaştın!")
            dungeon_enemies = [ # Zindana özel düşmanlar (isim, element)
                ("Mağara Trolü", Element.EARTH), 
                ("İskelet Savaşçısı", Element.ENERGY), # Enerji elementi olabilir
                ("Dev Örümcek", Element.EARTH), 
                ("Gölge Yaratığı", Element.ENERGY) # Özel element
            ]
            enemy_template_name, enemy_template_element = random.choice(dungeon_enemies)
            
            dungeon_opponent = choose_bender(f"{enemy_template_name} (Zindan)", enemy_template_element.name.lower())
            dungeon_opponent.level = max(1, bender.level + dungeon_level_bonus + random.randint(-1, 1))
            dungeon_opponent.base_power += random.randint(0, dungeon_level_bonus + 1)
            dungeon_opponent.base_max_health += random.randint(0, dungeon_level_bonus * 5)
            dungeon_opponent.update_stats_from_equipment()
            
            print(f"Karşına çıkan: {dungeon_opponent.name} (Seviye {dungeon_opponent.level})!")
            battle_result_dungeon = bender.battle(dungeon_opponent)
            if battle_result_dungeon == "lose":
                print("Zindanda yenildin ve kaçmak zorunda kaldın.")
                break # Zindandan çık
            elif battle_result_dungeon == "win":
                print("Canavarı yendin ve zindanda ilerlemeye devam ediyorsun.")
                # Görev güncellemesi
                for q in QUESTS:
                    if not q.is_completed or q.is_repeatable:
                        if q.quest_type == "combat" and "enemies_to_defeat" in q.requirements:
                            if enemy_template_name in q.requirements["enemies_to_defeat"]:
                                q.update_progress("enemy_defeated", 1, enemy_name=enemy_template_name)

        elif event_roll <= 75: # %30 Hazine (46-75)
            print("🗝️ Bir hazine sandığı buldun!")
            gold_found_dungeon = random.randint(bender.level * 8, bender.level * 20) + dungeon_level_bonus * 10
            bender.gold += gold_found_dungeon
            print(f"{gold_found_dungeon} altın kazandın!")
            
            # Rastgele bir eşya bulma şansı
            if random.random() < 0.4: # %40 şansla eşya
                # Zindana özel veya daha nadir eşyalar olabilir
                possible_dungeon_loot = [item for item in EQUIPMENT_ITEMS if item.rarity in [ItemRarity.RARE, ItemRarity.EPIC]]
                if not possible_dungeon_loot: # Eğer nadir eşya yoksa, herhangi birini seç
                    possible_dungeon_loot = SHOP_ITEMS + EQUIPMENT_ITEMS 
                
                if possible_dungeon_loot:
                    found_item_blueprint = random.choice(possible_dungeon_loot) 
                    # Eşyayı kopyala
                    if isinstance(found_item_blueprint, Equipment):
                        actual_found_item = Equipment(found_item_blueprint.name, found_item_blueprint.description, 
                                                found_item_blueprint.effect_type, found_item_blueprint.effect_amount, 
                                                found_item_blueprint.slot, found_item_blueprint.price, 
                                                found_item_blueprint.rarity, found_item_blueprint.max_durability)
                    else: # Item
                        actual_found_item = Item(found_item_blueprint.name, found_item_blueprint.description, 
                                            found_item_blueprint.effect_type, found_item_blueprint.effect_amount, 
                                            found_item_blueprint.price, found_item_blueprint.usage_limit, 
                                            found_item_blueprint.rarity)
                    bender.add_to_inventory(actual_found_item)
                    # print(f"Ayrıca bir '{actual_found_item.name}' [{actual_found_item.rarity.value}] buldun!") # add_to_inventory mesaj basar

        elif event_roll <= 90: # %15 Tuzak (76-90)
            print("🕸️ Bir tuzağa yakalandın!")
            trap_damage = random.randint(bender.max_health // 10, bender.max_health // 5) # Maks canın %10-%20'si hasar
            bender.take_damage(trap_damage)
            if bender.health <= 0:
                print("Zindanda tuzağa yenik düştün.")
                break # Zindandan çık
        else: # %10 Boş Oda veya küçük bir iyileşme (91-100)
            print("🚶 Oda şimdilik sakin görünüyor.")
            if random.random() < 0.3: # %30 şansla küçük bir dinlenme noktası
                print("Kısa bir mola verdin ve biraz enerji topladın.")
                bender.energy = min(bender.max_energy, bender.energy + bender.max_energy * 0.1) # %10 enerji yenile

    # Zindan sonu
    if bender.health > 0 and rooms_explored >= max_rooms_in_dungeon:
        print("\n🎉 Zindanı başarıyla tamamladın! 🎉")
        bonus_xp_dungeon = 100 + (bender.level * 15) + (dungeon_level_bonus * 20)
        bonus_gold_dungeon = random.randint(70, 120) + (bender.level * 8) + (dungeon_level_bonus * 15)
        bender.experience += bonus_xp_dungeon
        bender.gold += bonus_gold_dungeon
        print(f"🌟 {bonus_xp_dungeon} XP ve {bonus_gold_dungeon} altın kazandın!")
        # Zindan sonu özel ödül şansı
        if random.random() < 0.25 : # %25 şans
             legendary_loot_pool = [eq for eq in EQUIPMENT_ITEMS if eq.rarity == ItemRarity.LEGENDARY]
             epic_loot_pool = [eq for eq in EQUIPMENT_ITEMS if eq.rarity == ItemRarity.EPIC]
             rare_loot_pool = [eq for eq in EQUIPMENT_ITEMS if eq.rarity == ItemRarity.RARE]
             final_reward_item = None
             if random.random() < 0.1 and legendary_loot_pool : final_reward_item = random.choice(legendary_loot_pool) # %10 Efsanevi
             elif random.random() < 0.3 and epic_loot_pool : final_reward_item = random.choice(epic_loot_pool) # %30 Epik
             elif rare_loot_pool : final_reward_item = random.choice(rare_loot_pool) # Kalanı Nadir

             if final_reward_item:
                copied_reward = Equipment(final_reward_item.name, final_reward_item.description, final_reward_item.effect_type, final_reward_item.effect_amount, final_reward_item.slot, final_reward_item.price, final_reward_item.rarity, final_reward_item.max_durability)
                bender.add_to_inventory(copied_reward)
                print(f"🏆 Zindan sonu özel ödülü: '{copied_reward.name}' [{copied_reward.rarity.value}]!")
        bender._check_level_up()
    elif bender.health <= 0:
        print("\n😔 Zindanda bilincini kaybettin ve son anda dışarı çıkarıldın.")
        bender.health = max(1, int(original_health_before_dungeon * 0.1)) # Çok az canla başla
        bender.energy = int(original_energy_before_dungeon * 0.2)
        print("Biraz dinlenmen gerekecek.")
    else: # Erken çıkış (kaçtı veya başka bir sebep)
        print("\nZindandan ayrıldın.")

def crafting_menu(bender): # Bender nesnesi alır
    print("\n=== Zanaatkarlık Atölyesi 🔨 ===")
    
    while True: # Zanaat menüsünden çıkana kadar döngü
        print("\nMevcut Hammaddeleriniz:")
        resource_counts_in_inv = {} # Envanterdeki kaynakların sayımı
        for item_obj_craft in bender.inventory:
            if item_obj_craft.effect_type == "resource":
                resource_counts_in_inv[item_obj_craft.name] = resource_counts_in_inv.get(item_obj_craft.name, 0) + 1
        
        if not resource_counts_in_inv:
            print("  Hiç hammaddeniz yok. Keşif yaparak veya satın alarak hammadde toplayabilirsiniz.")
        else:
            for res_name_craft, count_craft in resource_counts_in_inv.items():
                print(f"- {res_name_craft}: {count_craft} adet")

        print("\nÜretebileceğiniz Tarifler:")
        craftable_recipes_display = [] # (recipe_name, recipe_data, can_craft_bool)
        
        # Tarifleri isme göre sırala
        sorted_recipe_names = sorted(CRAFTING_RECIPES.keys())

        for i, recipe_name_craft in enumerate(sorted_recipe_names, 1):
            recipe_data_craft = CRAFTING_RECIPES[recipe_name_craft]
            can_craft_this = True
            missing_materials_list = []
            materials_display_list = []
            for material_craft, count_needed_craft in recipe_data_craft["materials"].items():
                materials_display_list.append(f"{material_craft} x{count_needed_craft}")
                if resource_counts_in_inv.get(material_craft, 0) < count_needed_craft:
                    can_craft_this = False
                    missing_materials_list.append(f"{material_craft} (Eksik: {count_needed_craft - resource_counts_in_inv.get(material_craft, 0)})")
            
            output_item_craft = recipe_data_craft["output"] # Bu bir Item/Equipment nesnesi
            status_str_craft = "✅ Üretilebilir" if can_craft_this else f"❌ Eksik: {', '.join(missing_materials_list)}"
            
            print(f"{i}. {recipe_name_craft} [{output_item_craft.rarity.value}] - Malzemeler: {', '.join(materials_display_list)}")
            print(f"   Çıktı: {output_item_craft.description} - Durum: {status_str_craft}")
            craftable_recipes_display.append((recipe_name_craft, recipe_data_craft, can_craft_this))

        print("0. Geri")

        try:
            choice_input_craft = input("Üretmek istediğiniz tarifin numarası: ").strip()
            if not choice_input_craft.isdigit(): print("❌ Geçersiz giriş!"); continue
            
            selected_recipe_idx = int(choice_input_craft) -1
            if selected_recipe_idx == -1: return # 0. Geri
            
            if 0 <= selected_recipe_idx < len(craftable_recipes_display):
                selected_recipe_name_final, selected_recipe_data_final, can_craft_final = craftable_recipes_display[selected_recipe_idx]
                
                if can_craft_final:
                    confirm_craft = input(f"'{selected_recipe_name_final}' üretmek istediğinizden emin misiniz? (E/H): ").strip().lower()
                    if confirm_craft == 'e':
                        # Hammaddeleri envanterden kaldır
                        for material_to_remove, count_to_remove_craft in selected_recipe_data_final["materials"].items():
                            removed_so_far = 0
                            items_actually_removed_list = [] # Çıkarılacak nesnelerin listesi
                            for inv_item_craft_check in bender.inventory: # Envanteri dolaş
                                if inv_item_craft_check.name == material_to_remove and inv_item_craft_check.effect_type == "resource":
                                    if removed_so_far < count_to_remove_craft:
                                        items_actually_removed_list.append(inv_item_craft_check)
                                        removed_so_far += 1
                                    else: break # Gerekli sayıda bulundu
                            
                            for item_obj_to_delete_craft in items_actually_removed_list:
                                bender.remove_from_inventory(item_obj_to_delete_craft)
                            # print(f"- {removed_so_far} adet {material_to_remove} harcandı.") # remove_from_inventory mesaj basabilir

                        # Ürünü (kopya olarak) envantere ekle
                        output_item_blueprint_craft = selected_recipe_data_final["output"]
                        crafted_item_instance = None
                        if isinstance(output_item_blueprint_craft, Equipment):
                            crafted_item_instance = Equipment(output_item_blueprint_craft.name, output_item_blueprint_craft.description, 
                                                    output_item_blueprint_craft.effect_type, output_item_blueprint_craft.effect_amount, 
                                                    output_item_blueprint_craft.slot, output_item_blueprint_craft.price, 
                                                    output_item_blueprint_craft.rarity, output_item_blueprint_craft.max_durability)
                        else: # Item
                            crafted_item_instance = Item(output_item_blueprint_craft.name, output_item_blueprint_craft.description, 
                                                output_item_blueprint_craft.effect_type, output_item_blueprint_craft.effect_amount, 
                                                output_item_blueprint_craft.price, output_item_blueprint_craft.usage_limit, 
                                                output_item_blueprint_craft.rarity)
                        
                        if crafted_item_instance:
                            bender.add_to_inventory(crafted_item_instance)
                            # print(f"✅ {crafted_item_instance.name} başarıyla üretildi!") # add_to_inventory mesaj basar
                        else: # Beklenmedik
                            print("Üretim sırasında bir hata oluştu, ürün oluşturulamadı.")

                    else: print("Üretim iptal edildi.")
                else:
                    print("❌ Bu tarifi üretmek için yeterli malzemeniz yok.")
            else:
                print("❌ Geçersiz tarif seçimi!")
        except ValueError:
            print("❌ Geçersiz giriş! Lütfen bir sayı girin.")
        except Exception as e:
            print(f"Zanaat sırasında bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()


def visit_master(bender): # Bender nesnesi alır
    print("\n=== Usta Eğitimi 🧘 ===")
    print("Elementinizle ilgili usta bükücülerden özel yetenekler veya teknikler öğrenebilirsiniz.")
    
    # Usta yetenekleri daha güçlü veya özel olmalı
    masters_data = {
        Element.WATER: {"name": "Su Ustası Pakku", 
                        "abilities": [
                            Ability("Buz Duvarı", "Savunma için devasa bir buz duvarı oluşturur (Savaşta özel etki).", "buff_power", 10, 20, cooldown=4), # Güç buff'ı ile savunma simülasyonu
                            Ability("Ahtapot Formu", "Su kollarıyla çoklu saldırı yapar (Alan etkili).", "aoe_damage", 35, 25, cooldown=5)
                        ], "cost": 500, "reputation_req": 150, "level_req": 10},
        Element.FIRE: {"name": "Ateş Bilgesi Iroh", 
                       "abilities": [
                           Ability("Ejderha Nefesi", "Geniş alana yayılan güçlü bir ateş püskürtür.", "aoe_damage", 40, 30, cooldown=5),
                           Ability("Yıldırım Yönlendirme", "Gelen bir saldırıyı emer ve karşı saldırı yapar (Özel savaş mekaniği gerektirir).", "damage", 50, 35, cooldown=6) # Şimdilik normal hasar
                        ], "cost": 600, "reputation_req": 180, "level_req": 12},
        Element.EARTH: {"name": "Toprak Kralı Bumi", 
                        "abilities": [
                            Ability("Sismik Algı (Pasif)", "Düşmanların yerini daha iyi saptar (Kaçınma şansını azaltır gibi).", "debuff_opponent_power", -5, 0, is_active=False), # Rakibin gücünü azaltarak simüle edilebilir
                            Ability("Yer Sarsıntısı", "Tüm yerdeki düşmanları sersemletir ve hasar verir.", "aoe_damage", 30, 28, cooldown=5)
                        ], "cost": 550, "reputation_req": 160, "level_req": 11},
        Element.AIR: {"name": "Hava Keşişi Gyatso", 
                      "abilities": [
                          Ability("Hava Kalkanı Tornadosu", "Etrafında dönen bir hava kalkanı oluşturur (Geçici kaçınma artışı).", "crit_buff", 0.25, 15, cooldown=4), # crit_buff dodge için kullanılıyor
                          Ability("Mini Kasırga", "Düşmanı havaya savurur ve hasar verir.", "damage", 45, 25, cooldown=5)
                        ], "cost": 500, "reputation_req": 150, "level_req": 10},
        # EnergyBender için usta eklenebilir
    }

    if bender.element not in masters_data:
        print("Maalesef elementinize uygun bir usta bulunamadı.")
        return

    master_info_data = masters_data[bender.element]
    print(f"\n{master_info_data['name']} ile konuşuyorsunuz.")
    
    if bender.level < master_info_data["level_req"]:
        print(f"❌ Bu ustadan eğitim almak için çok tecrübesizsiniz. En az Seviye {master_info_data['level_req']} olmalısınız.")
        return
    if bender.gold < master_info_data["cost"]:
        print(f"❌ Yeterli altınınız yok. Eğitim maliyeti: {master_info_data['cost']} Altın.")
        return
    if bender.reputation < master_info_data["reputation_req"]:
        print(f"❌ Yeterli itibarınız yok. Gereken itibar: {master_info_data['reputation_req']}.")
        return
    
    learnable_master_abilities = []
    for ab_master in master_info_data["abilities"]: # ab_master olarak adlandıralım
        is_known = False
        for player_ab in bender.abilities:
            if player_ab.name == ab_master.name:
                is_known = True
                break
        if not is_known:
            learnable_master_abilities.append(ab_master)


    if not learnable_master_abilities:
        print(f"{master_info_data['name']} size öğretecek yeni bir yetenek kalmadığını söyledi.")
        return

    print("\nÖğrenebileceğiniz Yetenekler:")
    for i, ability_to_learn in enumerate(learnable_master_abilities, 1):
        status_type = " (Aktif Savaş Yeteneği)" if ability_to_learn.is_active else " (Pasif Yetenek)"
        print(f"{i}. {ability_to_learn.name}{status_type} - Maliyet: {ability_to_learn.energy_cost} Enerji (Kullanımda)")
        print(f"   Açıklama: {ability_to_learn.description}")
        if ability_to_learn.cooldown > 0 : print(f"   Bekleme Süresi: {ability_to_learn.cooldown} tur")
    print("0. Geri")

    try:
        choice_input_master = input(f"Öğrenmek istediğiniz yeteneğin numarası (Eğitim Bedeli: {master_info_data['cost']} Altın): ").strip()
        if not choice_input_master.isdigit(): print("❌ Geçersiz giriş!"); return
        
        selected_ability_idx = int(choice_input_master) -1
        if selected_ability_idx == -1: return # 0. Geri

        if 0 <= selected_ability_idx < len(learnable_master_abilities):
            selected_ability_to_learn = learnable_master_abilities[selected_ability_idx]
            confirm_learn = input(f"'{selected_ability_to_learn.name}' yeteneğini {master_info_data['cost']} altına öğrenmek istediğinizden emin misiniz? (E/H): ").strip().lower()
            if confirm_learn == 'e':
                bender.gold -= master_info_data["cost"]
                # bender.reputation -= 10 # İtibar harcanmasın, sadece gereksinim olsun
                
                # Yeteneği kopyalayarak öğrenelim
                new_learned_ability = Ability(
                    selected_ability_to_learn.name, selected_ability_to_learn.description,
                    selected_ability_to_learn.effect_type, selected_ability_to_learn.effect_amount,
                    selected_ability_to_learn.energy_cost, selected_ability_to_learn.is_active,
                    selected_ability_to_learn.cooldown, 0, selected_ability_to_learn.target_type
                )
                bender.learn_ability(new_learned_ability) # learn_ability mesaj basar
            else:
                print("Yetenek öğrenme iptal edildi.")
        else:
            print("❌ Geçersiz yetenek seçimi!")
    except ValueError:
        print("❌ Geçersiz giriş! Lütfen bir sayı girin.")


# Ana Oyun Döngüsü (Bu dosya direkt çalıştırılırsa diye)
def main_game_loop():
    active_benders_ingame = [] # Bu döngüye özel karakter listesi
    current_bender_ingame = None
    story_manager_ingame = StoryManager()
    # game_map zaten globalde tanımlı

    # Kayıt klasörünü oluştur (eğer yoksa)
    if not os.path.exists(SAVE_DIR): # SAVE_DIR globalde tanımlı olmalı ("saves")
        try:
            os.makedirs(SAVE_DIR)
        except OSError as e:
            print(f"HATA: Kayıt klasörü '{SAVE_DIR}' oluşturulamadı: {e}")
            return # Klasör yoksa ve oluşturulamıyorsa devam etme

    while True:
        print("\n" + "="*20 + " BÜKME DÜNYASI MACERASI " + "="*20)
        if current_bender_ingame:
            print(f"Aktif Karakter: {current_bender_ingame.name} ({current_bender_ingame.element.name.capitalize()}) | Seviye: {current_bender_ingame.level}")
            print(f"Konum: {game_map.get_current_location().name}") # game_map global olmalı
        else:
            print("Aktif Karakter: Yok")
            # Kayıtlı karakterleri yükle (eğer listede yoksa)
            if not active_benders_ingame:
                # Bu kısım main.py'deki load_characters_to_list gibi çalışabilir
                # Şimdilik basit tutalım, karakter seçimiyle yüklensin.
                pass


        print("\n--- ANA MENÜ (game.py) ---")
        print("1. Yeni Karakter Oluştur")
        print("2. Kayıtlı Karakter Yükle / Seç")
        if current_bender_ingame: # Aktif karakter varsa gösterilecek seçenekler
            print("3. Durum Görüntüle")
            print("4. Antrenman Yap")
            print("5. Savaş (Arena)")
            print("6. Dükkan")
            print("7. Envanter")
            print("8. Görevler")
            print("9. Hikaye İlerlemesi")
            print("10. Stat Puanı Dağıt")
            print("11. Keşfet / Konum Değiştir") 
            print("12. Zanaatkarlık") 
            print("13. Usta Eğitimi") 
            print("S. Oyunu Kaydet (Aktif Karakter)")
        print("L. Liderlik Tablosu (data.py'den)")
        print("X. Aktif Karakterden Çık / Değiştir")
        print("Q. Oyundan Çık")

        main_choice = input("Seçiminiz: ").strip().upper()

        if main_choice == "1":
            new_char_obj = create_character_interactive()
            if new_char_obj:
                # Listede aynı isimde var mı kontrol et, varsa üzerine yaz, yoksa ekle
                char_exists_idx = -1
                for idx, b in enumerate(active_benders_ingame):
                    if b.name == new_char_obj.name:
                        char_exists_idx = idx
                        break
                if char_exists_idx != -1:
                    if input(f"'{new_char_obj.name}' adında bir karakter zaten var. Üzerine yazılsın mı? (E/H): ").lower() == 'e':
                        active_benders_ingame[char_exists_idx] = new_char_obj
                        current_bender_ingame = new_char_obj
                        save_game(current_bender_ingame) # game.py'deki save_game
                    else:
                        print("Karakter oluşturma iptal edildi.")
                        new_char_obj = None # İşlem yapılmadı
                else:
                    active_benders_ingame.append(new_char_obj)
                    current_bender_ingame = new_char_obj
                    save_game(current_bender_ingame) # game.py'deki save_game
                
                if new_char_obj: print(f"'{current_bender_ingame.name}' aktif karakter.")

        elif main_choice == "2":
            # Kayıtlı karakterleri listele (SAVE_DIR içindeki .json dosyaları)
            if not os.path.exists(SAVE_DIR):
                print(f"Kayıt klasörü '{SAVE_DIR}' bulunamadı.")
                continue
            
            saved_char_files = [f.split('.')[0] for f in os.listdir(SAVE_DIR) if f.endswith(".json") and os.path.isfile(Path(SAVE_DIR) / f)]
            
            # Halihazırda yüklenmiş ama listede olmayanları da ekleyebiliriz (opsiyonel)
            # Şimdilik sadece dosyalardan yükleme.
            
            if not saved_char_files:
                print("Kayıtlı karakter bulunamadı.")
                continue
            
            print("\n=== Kayıtlı Karakterler ===")
            for i, char_file_name in enumerate(saved_char_files, 1):
                print(f"{i}. {char_file_name}")
            print("0. Geri")

            load_choice_input = input("Yüklemek/Seçmek istediğiniz karakterin numarası: ").strip()
            if load_choice_input.isdigit():
                load_choice_idx = int(load_choice_input) -1
                if load_choice_idx == -1: continue
                if 0 <= load_choice_idx < len(saved_char_files):
                    char_name_to_load = saved_char_files[load_choice_idx]
                    # Aktif listede var mı diye bak, varsa onu seç, yoksa yükle
                    loaded_bender_obj = None
                    for b_obj_check in active_benders_ingame:
                        if b_obj_check.name == char_name_to_load:
                            loaded_bender_obj = b_obj_check
                            print(f"'{char_name_to_load}' zaten yüklü, aktif karakter olarak ayarlandı.")
                            break
                    if not loaded_bender_obj: # Listede yoksa dosyadan yükle
                        loaded_bender_obj = load_game(char_name_to_load) # game.py'deki load_game
                        if loaded_bender_obj:
                            active_benders_ingame.append(loaded_bender_obj)
                    
                    if loaded_bender_obj:
                        current_bender_ingame = loaded_bender_obj
                        print(f"'{current_bender_ingame.name}' aktif karakter.")
                    # else: # load_game zaten hata mesajı basar
                else: print("❌ Geçersiz karakter seçimi.")
            else: print("❌ Lütfen bir sayı girin.")
        
        elif main_choice == "X": # Aktif karakterden çık
            current_bender_ingame = None
            print("Aktif karakterden çıkıldı. Yeni bir karakter seçin veya oluşturun.")

        elif main_choice == "L":
            from data import get_leaderboard as get_lb_from_data # data.py'den alalım
            leaderboard_list_data = get_lb_from_data()
            print("\n=== LİDERLİK TABLOSU 🏆 ===")
            if not leaderboard_list_data: print("Liderlik tablosu boş.")
            else:
                print(f"{'Sıra':<5} {'Ad':<20} {'Seviye':<10} {'Güç':<10} {'İtibar':<10} {'Element':<15}")
                print("-" * 75)
                for i, (name, level, power, reputation, element) in enumerate(leaderboard_list_data, 1):
                    el_display = element.replace("_", " ").title() if isinstance(element, str) else "Bilinmiyor"
                    print(f"{i:<5} {name:<20} {level:<10} {int(power):<10} {reputation:<10} {el_display:<15}")


        elif main_choice == "Q":
            if input("Değişiklikleri kaydetmeden çıkmak istediğinize emin misiniz? (E/H): ").strip().lower() == 'e':
                print("Oyundan çıkılıyor...")
                break # Ana döngüden çık
            else:
                print("Çıkış iptal edildi.")
        
        # Aktif karakter gerektiren işlemler:
        elif current_bender_ingame:
            if main_choice == "3": show_status(current_bender_ingame)
            elif main_choice == "4": train_character_action(current_bender_ingame)
            elif main_choice == "5": initiate_battle(active_benders_ingame) # Tüm listeyi yolla, içinden seçsin
            elif main_choice == "6": shop_menu(current_bender_ingame)
            elif main_choice == "7": inventory_menu(current_bender_ingame)
            elif main_choice == "8": manage_quests(current_bender_ingame)
            elif main_choice == "9": story_manager_ingame.show_story_progress(current_bender_ingame.name)
            elif main_choice == "10": distribute_stat_points(current_bender_ingame)
            elif main_choice == "11": # Keşfet / Konum Değiştir
                print("\n--- Konum Seçenekleri 🗺️ ---")
                print(f"Mevcut Konum: {game_map.get_current_location().name}")
                
                available_map_locations = list(game_map.locations.keys())
                for i, loc_map_name in enumerate(available_map_locations, 1):
                    loc_obj_map = game_map.locations[loc_map_name]
                    seviye_str = f"(Min. Sv: {loc_obj_map.min_level})" if loc_obj_map.min_level > 0 else ""
                    print(f"{i}. {loc_map_name} {seviye_str}")
                print("0. Geri (Keşif Menüsünden)")

                loc_choice_input = input("Gitmek istediğiniz konum (veya 0): ").strip()
                if loc_choice_input.isdigit():
                    loc_choice_idx = int(loc_choice_input) -1
                    if loc_choice_idx == -1: pass # Geri dön, ana menüye
                    elif 0 <= loc_choice_idx < len(available_map_locations):
                        target_loc_name = available_map_locations[loc_choice_idx]
                        if game_map.move_to(target_loc_name, current_bender_ingame.level): # Seviye kontrolü ile git
                            # Yeni konuma gelince otomatik keşif etkinliği
                            explore_location(current_bender_ingame, game_map) # Bu fonksiyon kendi içinde bir döngüye sahip olabilir
                    else: print("❌ Geçersiz konum seçimi.")
                else: print("❌ Lütfen bir sayı girin.")
            elif main_choice == "12": crafting_menu(current_bender_ingame)
            elif main_choice == "13": visit_master(current_bender_ingame)
            elif main_choice == "S": save_game(current_bender_ingame) # game.py'deki save_game
            else: print("❌ Geçersiz seçim veya aktif karakter gerektiren bir işlem seçildi.")
        
        else: # Aktif karakter yoksa ve seçim de karakter gerektirmeyenlerden değilse
            if main_choice not in ["1", "2", "L", "Q", "X"]: # Bu seçenekler karakter gerektirmez
                 print("❌ Bu işlem için önce bir karakter oluşturmalı veya seçmelisiniz.")

# Eğer bu dosya direkt çalıştırılırsa:
if __name__ == "__main__":
    # print("game.py direkt çalıştırıldı. Ana oyun döngüsü başlıyor...")
    # main_game_loop()
    # Normalde main.py'den çağrılması beklenir.
    # Direkt çalıştırma için bir test karakteri oluşturup bazı fonksiyonları deneyebilirsiniz.
    print("Bu dosya (game.py) normalde ana program (main.py) tarafından import edilmek içindir.")
    print("main.py dosyasını çalıştırarak oyunu başlatın.")
    # Örnek test:
    # test_player = create_character_interactive()
    # if test_player:
    #    show_status(test_player)
    #    shop_menu(test_player)