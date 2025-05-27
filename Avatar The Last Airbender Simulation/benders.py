import random
from enum import Enum

# Yeni Statlar ve Rarity için Enum'lar
class Element(Enum):
    WATER = 1
    FIRE = 2
    EARTH = 3
    AIR = 4
    ENERGY = 5

class BendingStyle(Enum):
    NORTHERN_WATER = 1
    SOUTHERN_WATER = 2
    SUN_WARRIOR_FIRE = 3
    ROUGE_FIRE = 4
    EARTH_RUMBLE_EARTH = 5
    SAND_BENDING_EARTH = 6
    AIR_NOMAD_AIR = 7
    FLIGHT_AIR = 8

class ItemRarity(Enum):
    COMMON = "Yaygın"
    UNCOMMON = "Nadir"
    RARE = "Nadir" # Türkçede aynı olabilir ama farklı sınıflarda kullanışlı
    EPIC = "Epik"
    LEGENDARY = "Efsanevi"

# Yeni Ability Sınıfı
class Ability:
    def __init__(self, name, description, effect_type, effect_amount, energy_cost, is_active=True, cooldown=0, current_cooldown=0, target_type="opponent"):
        self.name = name
        self.description = description
        self.effect_type = effect_type # "damage", "heal", "buff_power", "debuff_opponent", "crit_buff"
        self.effect_amount = effect_amount
        self.energy_cost = energy_cost
        self.is_active = is_active # True for combat abilities, False for passive buffs
        self.cooldown = cooldown # Turn-based cooldown
        self.current_cooldown = current_cooldown # Mevcut bekleme süresi
        self.target_type = target_type # "opponent", "self", "all_opponents", etc.

    def use(self, caster, target=None):
        if self.is_active:
            if caster.energy < self.energy_cost:
                print(f"❌ Yeterli enerji yok! ({self.energy_cost} enerji gerekli)")
                return False
            if self.current_cooldown > 0:
                print(f"⏳ {self.name} beklemede. Kalan süre: {self.current_cooldown} tur.")
                return False
            
            caster.energy -= self.energy_cost
            self.current_cooldown = self.cooldown

            print(f"✨ {caster.name}, {self.name} yeteneğini kullanıyor! {self.description}")
            
            if self.effect_type == "damage":
                if target:
                    damage = self.effect_amount + (caster.power * 0.75) 
                    target.take_damage(damage)
                    print(f"{target.name} {int(damage)} hasar aldı!")
                    if target.health <= 0:
                        print(f"{target.name} yenildi!")
                        return "defeated"
                else:
                    print("Hedef yok!")
            elif self.effect_type == "heal":
                caster.heal(self.effect_amount + (caster.level * 2)) 
                print(f"{caster.name} {int(self.effect_amount + (caster.level * 2))} can yeniledi.")
            elif self.effect_type == "buff_power":
                caster.apply_buff("power_boost", self.effect_amount, 3) 
                print(f"{caster.name}'ın gücü {self.effect_amount} arttı!")
            elif self.effect_type == "crit_buff":
                caster.apply_buff("crit_chance_boost", self.effect_amount, 2)
                print(f"{caster.name}'ın kritik vuruş şansı {self.effect_amount}% arttı!")
            elif self.effect_type == "debuff_opponent_power":
                if target:
                    target.apply_debuff("power_reduce", self.effect_amount, 2) 
                    print(f"{target.name}'ın gücü {self.effect_amount} azaldı!")
            elif self.effect_type == "aoe_damage": 
                print("Alan etkili bir saldırı yapılıyor!")
                if target: # Şimdilik tek hedefli gibi davranıyor, savaş sistemi geliştirilirse burası güncellenmeli
                    damage = self.effect_amount + (caster.power * 0.5)
                    target.take_damage(damage)
                    print(f"{target.name} {int(damage)} hasar aldı!")
                    if target.health <= 0:
                        print(f"{target.name} yenildi!")
                        return "defeated"
            
            return True
        else: 
            print(f"{self.name} pasif yeteneği zaten aktif.")
            return False

    def tick_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def to_dict(self):
        return self.__dict__


# Item Sınıfı - Rarity ve kullanım limiti eklendi
class Item:
    def __init__(self, name, description, effect_type, effect_amount, price, usage_limit=1, rarity=ItemRarity.COMMON):
        self.name = name
        self.description = description
        self.effect_type = effect_type # "health", "xp", "gold", "reputation", "power", "energy", "ability", "resource"
        self.effect_amount = effect_amount
        self.price = price
        self.usage_limit = usage_limit # 0 ise sınırsız (kaynaklar gibi)
        self.rarity = rarity

    def use(self, bender):
        if self.effect_type == "resource":
            print(f"❌ {self.name} bir hammaddedir ve doğrudan kullanılamaz.")
            return False
        if self.usage_limit == 0 or self.usage_limit > 0: # usage_limit 0 ise sınırsız
            print(f"✨ {bender.name}, {self.name} kullanıyor! {self.description}")
            if self.effect_type == "health":
                bender.heal(self.effect_amount)
                # print(f"{self.effect_amount} can yenilendi.") # heal metodu zaten mesaj basıyor
            elif self.effect_type == "xp":
                bender.experience += self.effect_amount
                print(f"{self.effect_amount} XP kazandınız.")
                bender._check_level_up()
            elif self.effect_type == "gold":
                bender.gold += self.effect_amount
                print(f"{self.effect_amount} altın kazandınız.")
            elif self.effect_type == "reputation":
                bender.reputation += self.effect_amount
                print(f"{self.effect_amount} itibar kazandınız.")
            elif self.effect_type == "power": # Bu genelde geçici buff olmalı, kalıcı için quest/level up
                bender.power += self.effect_amount # Ya da buff olarak ekle
                print(f"{self.effect_amount} güç kazandınız (geçici veya kalıcı etki).")
            elif self.effect_type == "energy":
                bender.energy = min(bender.max_energy, bender.energy + self.effect_amount)
                print(f"{self.effect_amount} enerji yenilendi.")
            elif self.effect_type == "ability":
                new_ability_name = self.effect_amount
                if bender.learn_ability_by_name(new_ability_name):
                    print(f"🎉 {new_ability_name} yeteneğini öğrendiniz!")
                else:
                    print(f"Bu yeteneği öğrenemediniz veya zaten biliyorsunuz.")
                    return False 
            
            if self.usage_limit > 0: # Sınırsız değilse azalt
                self.usage_limit -= 1
            return True
        else:
            print(f"❌ {self.name} için kullanım hakkınız bitti.")
            return False

    def to_dict(self):
        data = self.__dict__.copy()
        data['rarity'] = self.rarity.name  # Enum'ı string olarak kaydet
        return data

# Equipment Sınıfı - Slot, Rarity ve Dayanıklılık eklendi
class Equipment(Item):
    def __init__(self, name, description, effect_type, effect_amount, slot, price, rarity=ItemRarity.COMMON, durability=100):
        super().__init__(name, description, effect_type, effect_amount, price, usage_limit=0, rarity=rarity) # Equipment'lar genelde sınırsız kullanımlı
        self.slot = slot 
        self.durability = durability 
        self.max_durability = durability

    def equip(self, bender):
        # Aynı slottaki önceki ekipmanı çıkar ve envantere ekle
        removed_equipped_item = None
        for equipped_item in bender.equipped_items:
            if equipped_item.slot == self.slot:
                removed_equipped_item = equipped_item
                break # Döngüden çık ki listeyi değiştirirken sorun olmasın
        
        if removed_equipped_item:
            removed_equipped_item.unequip(bender) # Bu, bender.equipped_items'tan çıkarır
            bender.add_to_inventory(removed_equipped_item) # Envantere ekle
            print(f"'{removed_equipped_item.name}' çıkarıldı ve envanterinize eklendi.")

        if self in bender.inventory:
             bender.remove_from_inventory(self) 
        bender.equipped_items.append(self)
        # bender.apply_equipment_effect(self) # Bu artık update_stats_from_equipment içinde olmalı
        print(f"💪 {self.name} kuşanıldı! ({self.slot.capitalize()} slotunda)")
        bender.update_stats_from_equipment() 

    def unequip(self, bender):
        if self in bender.equipped_items:
            bender.equipped_items.remove(self)
            # bender.remove_equipment_effect(self) # Bu artık update_stats_from_equipment içinde olmalı
            print(f"➖ {self.name} çıkarıldı.")
            bender.update_stats_from_equipment() 
            return True
        return False
    
    def take_damage(self, amount): # Ekipman hasar aldığında
        self.durability = max(0, self.durability - int(amount)) # Hasarı tamsayı yapalım
        if self.durability == 0:
            print(f"⚠️ {self.name} hasar görmekten kırıldı ve kullanılamaz hale geldi!")
            # Otomatik çıkarma veya kırık item olarak işaretleme eklenebilir
        
    def repair(self):
        self.durability = self.max_durability
        print(f"🛠️ {self.name} tamir edildi.")

    def to_dict(self):
        data = super().to_dict() # Item.to_dict() çağrılır (rarity.name içerir)
        return data


# Bender Sınıfı - Yeni statlar ve yetenek yönetimi eklendi
class Bender:
    def __init__(self, name, element, bending_style=None):
        self.name = name
        self.element = Element[element.upper()]
        self.bending_style = BendingStyle[f"{bending_style.upper()}_{element.upper()}"] if bending_style and element else None
        
        self.level = 1
        self.experience = 0
        self.gold = 100
        self.reputation = 0
        self.train_count = 0
        self.stat_points = 0 

        self.base_max_health = 100
        self.base_power = 10
        self.base_max_energy = 50
        
        # Türetilmiş statlar başlangıçta base değerlere eşit + seviye bonusu
        # Bu değerler update_stats_from_equipment ile güncellenecek
        self.max_health = self.base_max_health
        self.health = self.max_health
        self.power = self.base_power
        self.max_energy = self.base_max_energy
        self.energy = self.max_energy

        self.inventory = []
        self.equipped_items = []

        self.abilities = [] # Başlangıçta boş, _get_initial_abilities ile dolacak
        self.active_abilities = [] 
        self.passive_abilities = [] 
        self._get_initial_abilities() # Yetenekleri __init__ sonunda yükle

        self.special_abilities_unlocked = [] 

        self.crit_chance = 0.05 
        self.dodge_chance = 0.05 

        self.buffs = {} 
        self.debuffs = {} 

        self._check_level_up() 
        self.update_stats_from_equipment() # Ekipman ve seviyeye göre statları ilk ayarla

    def _get_initial_abilities(self):
        # Her elemente özel başlangıç yetenekleri (Ability nesneleri olarak)
        # Bu metod artık doğrudan self.abilities listesini dolduracak
        # learn_ability ile eklenerek mükerrer kontrolü sağlanacak
        initial_abilities_to_learn = []
        if self.element == Element.WATER:
            initial_abilities_to_learn.append(Ability("Su Topu", "Temel bir su saldırısı.", "damage", 15, 5))
            if self.bending_style == BendingStyle.SOUTHERN_WATER:
                initial_abilities_to_learn.append(Ability("Şifa Suyu", "Kendini iyileştirir.", "heal", 20, 10))
        elif self.element == Element.FIRE:
            initial_abilities_to_learn.append(Ability("Ateş Topu", "Temel bir ateş saldırısı.", "damage", 18, 6))
            if self.bending_style == BendingStyle.ROUGE_FIRE:
                initial_abilities_to_learn.append(Ability("Alev Patlaması", "Yüksek hasar veren, riskli bir saldırı.", "damage", 30, 15))
        elif self.element == Element.EARTH:
            initial_abilities_to_learn.append(Ability("Kaya Fırlatma", "Temel bir toprak saldırısı.", "damage", 20, 7))
            if self.bending_style == BendingStyle.EARTH_RUMBLE_EARTH:
                initial_abilities_to_learn.append(Ability("Taş Kalkan", "Gelen hasarı azaltır (Güç artışı olarak simüle).", "buff_power", 5, 8, is_active=True)) # Örnek: geçici savunma buff'ı
        elif self.element == Element.AIR:
            initial_abilities_to_learn.append(Ability("Hava Süpürgesi", "Temel bir hava saldırısı.", "damage", 12, 4))
            if self.bending_style == BendingStyle.FLIGHT_AIR:
                initial_abilities_to_learn.append(Ability("Hızlı Kaçınma", "Kaçınma şansını artırır.", "crit_buff", 0.20, 7, is_active=True)) # crit_buff burada dodge_buff olarak kullanılabilir
        elif self.element == Element.ENERGY:
            initial_abilities_to_learn.append(Ability("Enerji Patlaması", "Temel bir enerji saldırısı.", "damage", 25, 10))
        
        for ab in initial_abilities_to_learn:
            self.learn_ability(ab) # Mükerrer kontrolü ile ekle
        
        # self.active_abilities ve self.passive_abilities learn_ability içinde güncelleniyor

    def learn_ability(self, new_ability: Ability):
        if new_ability.name not in [a.name for a in self.abilities]:
            self.abilities.append(new_ability)
            if new_ability.is_active:
                self.active_abilities.append(new_ability)
            else:
                self.passive_abilities.append(new_ability)
                # Pasif yeteneklerin etkileri hemen uygulanabilir veya update_stats içinde kontrol edilebilir
                if new_ability.effect_type == "dodge_chance_boost" and not new_ability.is_active: # Örnek pasif etki
                    self.dodge_chance += new_ability.effect_amount 
            print(f"🎉 {self.name}, yeni yetenek '{new_ability.name}' öğrendi!")
            return True
        else:
            print(f"😔 {self.name} zaten '{new_ability.name}' yeteneğini biliyor.")
            return False

    def learn_ability_by_name(self, ability_name):
        all_possible_abilities = [
            Ability("Gelgit Dalgası", "Büyük bir su dalgası fırlatır.", "aoe_damage", 30, 20, cooldown=3),
            Ability("Mavi Alev", "Daha yoğun, yıkıcı bir ateş fırlatır.", "damage", 40, 25, cooldown=3),
            Ability("Lav Bükme", "Toprağı lavlara çevirir.", "aoe_damage", 35, 22, cooldown=3),
            Ability("Uçma", "Hava akımlarıyla uçarak kaçınma sağlar.", "dodge_chance_boost", 0.15, 0, is_active=False), 
            Ability("Kan Bükme", "Düşmanın kanını kontrol eder (Sadece Su Bükücü - ÇOK NADİR).", "debuff_opponent_power", 50, 40, cooldown=5), 
            Ability("Yıldırım Bükme", "Şimşek fırlatır (Sadece Ateş Bükücü).", "damage", 60, 35, cooldown=4),
            Ability("Metal Bükme", "Metali büker (Sadece Toprak Bükücü).", "damage", 55, 30, cooldown=4),
            Ability("Hava Patlaması", "Güçlü bir hava dalgası yayar.", "aoe_damage", 45, 28, cooldown=3),
            Ability("Kritik Vuruş Gelişimi", "Kritik vuruş şansını kalıcı artırır.", "crit_buff", 0.03, 0, is_active=False),
            Ability("Enerji Absorpsiyonu", "Saldırıdan enerji çalar.", "energy", 10, 0, is_active=False), 
        ]
        selected_ability_blueprint = next((a for a in all_possible_abilities if a.name == ability_name), None)

        if selected_ability_blueprint:
            # Element uygunluğu kontrolü (kitap isimlerine göre)
            # Bu kontrol SHOP_ITEMS içinde yapılmalı, burada sadece öğrenme
            
            # Yeteneği kopyala ki cooldown gibi durumları etkilemesin
            new_ability = Ability(
                selected_ability_blueprint.name, selected_ability_blueprint.description,
                selected_ability_blueprint.effect_type, selected_ability_blueprint.effect_amount,
                selected_ability_blueprint.energy_cost, selected_ability_blueprint.is_active,
                selected_ability_blueprint.cooldown, 0, selected_ability_blueprint.target_type
            )
            return self.learn_ability(new_ability)
        return False

    def _check_level_up(self):
        leveled_up = False
        while self.experience >= 100 * self.level:
            leveled_up = True
            self.experience -= (100 * self.level)
            self.level += 1
            # Temel stat artışları burada yapılmamalı, update_stats_from_equipment'e bırakılmalı.
            # Sadece base_stat'lar güncellenebilir veya seviye bonusu update_stats'ta hesaplanabilir.
            # Şimdilik eski mantıkla devam edip, update_stats'ın bunu doğru yönettiğini varsayalım.
            # self.max_health += 20 # Bu satırlar update_stats_from_equipment tarafından yönetilecek
            # self.power += 5
            # self.max_energy += 10
            self.health = self.max_health # Can fullenir (update_stats sonrası)
            self.energy = self.max_energy # Enerji fullenir (update_stats sonrası)
            self.stat_points += 3 
            print(f"\n🎉 {self.name} seviye {self.level} oldu! Tüm can ve enerji yenilendi. {self.stat_points} stat puanı kazandınız! 🎉")

            if self.level % 5 == 0: 
                # self.crit_chance += 0.01 # update_stats_from_equipment yönetecek
                # self.dodge_chance += 0.01
                print("Kritik vuruş ve kaçınma şansınız seviye bonusuyla arttı (stat güncellemesinde yansıyacak)!")
            
            if self.level >= 10 and self.bending_style and self.bending_style not in self.special_abilities_unlocked:
                print(f"✨ Element stilinizle ilgili yeni özel yetenekler açıldı: {self.bending_style.name.replace('_', ' ')}!")
                self.special_abilities_unlocked.append(self.bending_style)
                if self.bending_style == BendingStyle.SOUTHERN_WATER:
                    print("Şifa yetenekleriniz güçlendi!")
                    self.learn_ability(Ability("Kan Bükme (Gelişmiş)", "Düşmanın kanını kontrol eder ve güçlü hasar verir.", "damage", 70, 50, cooldown=5))
                elif self.bending_style == BendingStyle.ROUGE_FIRE:
                    print("Ateş patlamalarınız daha yıkıcı!")
                    self.learn_ability(Ability("Yıldırım Bükme (Gelişmiş)", "Yüksek hasarlı yıldırım fırlatır.", "damage", 80, 55, cooldown=5))
        
        if leveled_up:
            self.update_stats_from_equipment() # Seviye atlama sonrası statları güncelle
            self.health = self.max_health # Canı full yap
            self.energy = self.max_energy # Enerjiyi full yap


    def apply_buff(self, buff_type, amount, duration):
        # Buff'ı uygulamadan önce, eğer varsa eski buff'ı kaldır
        if buff_type in self.buffs:
            self.remove_buff(buff_type, self.buffs[buff_type]["amount"])

        self.buffs[buff_type] = {"amount": amount, "duration": duration}
        if buff_type == "power_boost":
            self.power += amount
        elif buff_type == "crit_chance_boost":
            self.crit_chance += amount
        self.update_stats_from_equipment() # Buff sonrası statları güncellemek için çağırılabilir veya doğrudan uygulanabilir.
                                         # Şimdilik doğrudan uyguluyoruz, update_stats bunu zaten hesaba katacak.

    def remove_buff(self, buff_type, amount):
        if buff_type == "power_boost":
            self.power = max(self.base_power + (self.level-1)*5, self.power - amount) # Ekipmansız temel gücün altına düşmesin
        elif buff_type == "crit_chance_boost":
            self.crit_chance = max(0.05 + ((self.level-1)//5 * 0.01), self.crit_chance - amount) 
        # self.update_stats_from_equipment() # Gerekirse

    def apply_debuff(self, debuff_type, amount, duration):
        if debuff_type in self.debuffs: # Eski debuff'ı kaldır (etkisini geri alarak)
             self.remove_debuff(debuff_type, self.debuffs[debuff_type]["amount"])

        self.debuffs[debuff_type] = {"amount": amount, "duration": duration}
        if debuff_type == "power_reduce":
            self.power = max(1, self.power - amount) 
        # self.update_stats_from_equipment()

    def remove_debuff(self, debuff_type, amount):
        if debuff_type == "power_reduce":
            self.power += amount # Debuff etkisi geri eklenir
        # self.update_stats_from_equipment()


    def tick_buffs_debuffs(self):
        buffs_to_remove = []
        for buff_type, data in list(self.buffs.items()): # list() ile kopyasını al
            data["duration"] -= 1
            if data["duration"] <= 0:
                print(f"Buff sona erdi: {buff_type}")
                self.remove_buff(buff_type, data["amount"])
                buffs_to_remove.append(buff_type)
        for buff_type in buffs_to_remove:
            del self.buffs[buff_type]

        debuffs_to_remove = []
        for debuff_type, data in list(self.debuffs.items()): # list() ile kopyasını al
            data["duration"] -= 1
            if data["duration"] <= 0:
                print(f"Debuff sona erdi: {debuff_type}")
                self.remove_debuff(debuff_type, data["amount"])
                debuffs_to_remove.append(debuff_type)
        for debuff_type in debuffs_to_remove:
            del self.debuffs[debuff_type]

        for ability in self.active_abilities:
            ability.tick_cooldown()
        
        # Pasif yeteneklerin periyodik etkileri (örn: her tur can yenileme)
        for p_ability in self.passive_abilities:
            if p_ability.effect_type == "heal" and p_ability.energy_cost == 0: # Örnek: bedelsiz pasif can yenileme
                self.heal(p_ability.effect_amount)
                print(f"(Pasif) {p_ability.name} ile {p_ability.effect_amount} can yenilendi.")


    def train(self):
        xp_gain = random.randint(10, 30) + self.level * 2 # Seviyeye göre biraz artsın
        self.experience += xp_gain
        self.train_count += 1 
        self._check_level_up()
        return xp_gain
    
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
        print(f"❤️ {self.name}, {int(amount)} can yeniledi. Güncel can: {self.health}/{self.max_health}")

    def take_damage(self, amount):
        effective_amount = int(amount) # Hasar tamsayı olmalı
        self.health -= effective_amount
        print(f"💔 {self.name}, {effective_amount} hasar aldı. Güncel can: {self.health}/{self.max_health}")
        if self.health <= 0:
            self.health = 0 # Can 0'ın altına düşmesin
            print(f"💀 {self.name} bilincini kaybetti!")

        for item in self.equipped_items:
            if item.slot == "armor" and isinstance(item, Equipment): # isinstance kontrolü eklendi
                item.take_damage(effective_amount * 0.1) 

    def add_to_inventory(self, item):
        self.inventory.append(item)
        print(f"🎒 {item.name} envanterinize eklendi.")

    def remove_from_inventory(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            # print(f"🗑️ {item.name} envanterinizden çıkarıldı.") # İsteğe bağlı mesaj
            return True
        print(f"🔍 {item.name} envanterinizde bulunamadı.")
        return False
    
    def apply_equipment_effect(self, equipment):
        # Bu metod artık update_stats_from_equipment içinde toplu olarak yönetiliyor.
        # Doğrudan çağrılmasına gerek kalmadı, ancak mantığı update_stats'a taşındı.
        pass

    def remove_equipment_effect(self, equipment):
        # Bu metod artık update_stats_from_equipment içinde toplu olarak yönetiliyor.
        pass

    def update_stats_from_equipment(self):
        # Önce temel seviye bonuslarını hesapla
        self.max_health = self.base_max_health + (self.level - 1) * 20 
        self.power = self.base_power + (self.level - 1) * 5
        self.max_energy = self.base_max_energy + (self.level - 1) * 10
        self.crit_chance = 0.05 + ((self.level -1) // 5 * 0.01) 
        self.dodge_chance = 0.05 + ((self.level -1) // 5 * 0.01)

        # Stat puanlarını uygula (bu kısım distribute_stat_points fonksiyonu ile yönetilmeli
        # ve base_stat'ları artırmalı, şimdilik burada değil)
        # Eğer stat puanları doğrudan max_health, power gibi değerleri artırıyorsa,
        # o zaman bu fonksiyonun en sonunda uygulanmalı veya base değerlere eklenmeli.
        # Örnek: self.max_health += self.distributed_health_points (yeni bir özellik)

        # Ekipman etkilerini uygula
        for eq in self.equipped_items:
            if eq.effect_type == "health_boost":
                self.max_health += eq.effect_amount
            elif eq.effect_type == "power_boost":
                self.power += eq.effect_amount
            elif eq.effect_type == "energy_boost":
                self.max_energy += eq.effect_amount
            elif eq.effect_type == "crit_chance_boost":
                self.crit_chance += eq.effect_amount
            elif eq.effect_type == "dodge_chance_boost":
                self.dodge_chance += eq.effect_amount
        
        # Pasif yeteneklerin kalıcı stat etkilerini uygula
        for p_ability in self.passive_abilities:
            if p_ability.effect_type == "crit_buff" and not p_ability.is_active: # Kalıcı kritik artışı
                self.crit_chance += p_ability.effect_amount
            elif p_ability.effect_type == "dodge_chance_boost" and not p_ability.is_active: # Kalıcı kaçınma artışı
                self.dodge_chance += p_ability.effect_amount
            # Diğer pasif stat artışları eklenebilir

        # Buff ve Debuff'ları uygula (tick_buffs_debuffs içinde zaten anlık değerler güncelleniyor,
        # burası daha çok max değerleri etkileyen bufflar için olabilir veya gerekmiyebilir)
        # Genelde buff/debuff anlık power, crit_chance gibi değerleri değiştirir.
        # Eğer max_health gibi değerleri değiştiriyorsa burada da yansıtılmalı.
        # Şimdilik tick_buffs_debuffs'in anlık statları yönettiğini varsayıyoruz.

        # Can ve enerji max'ı geçmesin veya 0'ın altına düşmesin
        self.health = min(self.health, self.max_health)
        self.energy = min(self.energy, self.max_energy)
        self.health = max(0, self.health) # Hasar sonrası 0'ın altına düşebilir, düzelt.
        self.energy = max(0, self.energy)

    def battle(self, opponent):
        print(f"\n--- SAVAŞ BAŞLADI: {self.name} ({self.health}/{self.max_health} ❤️, {self.energy}/{self.max_energy} ⚡) vs {opponent.name} ({opponent.health}/{opponent.max_health} ❤️, {opponent.energy}/{opponent.max_energy} ⚡) ---")
        
        # Savaş öncesi can ve enerji tamamlama (isteğe bağlı, oyun tasarımına göre)
        # self.health = self.max_health
        # self.energy = self.max_energy
        # opponent.health = opponent.max_health
        # opponent.energy = opponent.max_energy

        turn = 0
        while self.health > 0 and opponent.health > 0:
            turn += 1
            print(f"\n--- TUR {turn} ---")
            
            self.tick_buffs_debuffs()
            opponent.tick_buffs_debuffs()

            if self.health <= 0: # Tur başında kontrol
                print(f"😔 {self.name} savaşı kaybetti (tur başında)!")
                return "lose"
            if opponent.health <= 0: # Tur başında kontrol
                print(f"🎉 {self.name} savaşı kazandı (tur başında)! 🎉")
                # Ödüller burada da verilebilir veya sadece savaş sonunda
                return "win"


            # Oyuncu Hamlesi
            print(f"\n{self.name}'ın Hamlesi (Can: {int(self.health)}/{int(self.max_health)}, Enerji: {int(self.energy)}/{int(self.max_energy)})")
            print("1. Saldır (Temel Bükme)")
            
            available_abilities = [ab for ab in self.active_abilities if ab.current_cooldown == 0 and self.energy >= ab.energy_cost]
            if available_abilities:
                print("2. Yetenek Kullan")
                for i, ab in enumerate(available_abilities):
                    print(f"   {i+1}. {ab.name} (Enerji: {ab.energy_cost}, Bekleme: {ab.cooldown} tur, Mevcut Bekleme: {ab.current_cooldown}) - {ab.description}")
            
            print("3. İksir Kullan (Envanterden)")
            print("4. Kaç")

            action_choice = input("Seçiminiz: ")
            
            player_action_taken = False
            if action_choice == "1":
                player_action_taken = True
                is_crit = random.random() < self.crit_chance
                damage = self.power * (1.5 if is_crit else 1) 
                print(f"🔥 {self.name} temel bükme saldırısı yapıyor! {'(KRİTİK VURUŞ!)' if is_crit else ''}")
                if random.random() < opponent.dodge_chance:
                    print(f"💨 {opponent.name} saldırıdan kaçtı!")
                else:
                    opponent.take_damage(damage)
            elif action_choice == "2" and available_abilities:
                player_action_taken = True
                try:
                    ability_choice_input = input("Kullanmak istediğiniz yeteneğin numarası: ")
                    ability_index = int(ability_choice_input) - 1
                    if 0 <= ability_index < len(available_abilities):
                        selected_ability = available_abilities[ability_index]
                        use_result = selected_ability.use(self, opponent)
                        if use_result == "defeated":
                            print(f"🎉 {self.name} savaşı kazandı! 🎉")
                            self.experience += 50 + (opponent.level * 10)
                            self.gold += 20 + (opponent.level * 5)
                            self.reputation += 5
                            self._check_level_up()
                            return "win"
                    else:
                        print("❌ Geçersiz yetenek seçimi. Temel saldırı yapılıyor.")
                        # Fallback to basic attack or re-prompt
                        is_crit = random.random() < self.crit_chance
                        damage = self.power * (1.5 if is_crit else 1)
                        if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                        else: opponent.take_damage(damage)

                except ValueError:
                    print("❌ Geçersiz giriş. Temel saldırı yapılıyor.")
                    is_crit = random.random() < self.crit_chance
                    damage = self.power * (1.5 if is_crit else 1)
                    if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                    else: opponent.take_damage(damage)
            elif action_choice == "3":
                player_action_taken = True
                usable_potions = [item for item in self.inventory if isinstance(item, Item) and not isinstance(item, Equipment) and item.effect_type in ["health", "energy"] and item.usage_limit != 0] # Sadece Item, Equipment değil
                if not usable_potions:
                    print("❌ Kullanılabilecek iksiriniz yok. Temel saldırı yapılıyor.")
                    is_crit = random.random() < self.crit_chance
                    damage = self.power * (1.5 if is_crit else 1)
                    if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                    else: opponent.take_damage(damage)
                else:
                    print("\nKullanılabilir İksirler:")
                    for i, potion in enumerate(usable_potions):
                        print(f"{i+1}. {potion.name} ({potion.description}) (Kalan: {'Sınırsız' if potion.usage_limit == 0 else potion.usage_limit})")
                    
                    potion_choice_input = input("Kullanmak istediğiniz iksirin numarası (0: Geri/Saldır): ")
                    try:
                        potion_choice_idx = int(potion_choice_input) -1
                        if potion_choice_idx == -1 : # Geri seçeneği temel saldırıya dönsün
                             print("Temel saldırı yapılıyor.")
                             is_crit = random.random() < self.crit_chance
                             damage = self.power * (1.5 if is_crit else 1)
                             if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                             else: opponent.take_damage(damage)
                        elif 0 <= potion_choice_idx < len(usable_potions):
                            selected_potion = usable_potions[potion_choice_idx]
                            if selected_potion.use(self):
                                if selected_potion.usage_limit == 0 and selected_potion.name in [inv_item.name for inv_item in self.inventory]: # Kullanım limiti 0 olduysa ve hala envanterdeyse
                                    self.remove_from_inventory(selected_potion)
                            else: # Kullanım başarısız olursa
                                print("İksir kullanılamadı. Temel saldırı yapılıyor.")
                                is_crit = random.random() < self.crit_chance
                                damage = self.power * (1.5 if is_crit else 1)
                                if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                                else: opponent.take_damage(damage)
                        else:
                            print("❌ Geçersiz iksir seçimi. Temel saldırı yapılıyor.")
                            is_crit = random.random() < self.crit_chance
                            damage = self.power * (1.5 if is_crit else 1)
                            if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                            else: opponent.take_damage(damage)
                    except ValueError:
                        print("❌ Geçersiz giriş. Temel saldırı yapılıyor.")
                        is_crit = random.random() < self.crit_chance
                        damage = self.power * (1.5 if is_crit else 1)
                        if random.random() < opponent.dodge_chance: print(f"💨 {opponent.name} saldırıdan kaçtı!")
                        else: opponent.take_damage(damage)
            elif action_choice == "4":
                player_action_taken = True
                run_chance = 0.5 + (self.level / opponent.level * 0.1) if opponent.level > 0 else 0.5 
                if random.random() < run_chance:
                    print("🏃 Savaş alanından kaçtınız!")
                    return "ran_away"
                else:
                    print("❌ Kaçamadınız! Rakip sizi yakaladı.")
            else: # Geçersiz seçim veya yetenek yoksa
                if not player_action_taken: # Eğer yukarıdaki hiçbir koşul oyuncu eylemini gerçekleştirmediyse
                    print("❌ Geçersiz seçim veya eylem. Temel saldırı yapılıyor.")
                    is_crit = random.random() < self.crit_chance
                    damage = self.power * (1.5 if is_crit else 1)
                    print(f"🔥 {self.name} temel bükme saldırısı yapıyor! {'(KRİTİK VURUŞ!)' if is_crit else ''}")
                    if random.random() < opponent.dodge_chance:
                        print(f"💨 {opponent.name} saldırıdan kaçtı!")
                    else:
                        opponent.take_damage(damage)


            if opponent.health <= 0:
                print(f"🎉 {self.name} savaşı kazandı! 🎉")
                self.experience += 50 + (opponent.level * 10)
                self.gold += 20 + (opponent.level * 5)
                self.reputation += 5
                self._check_level_up()
                return "win"
            
            # Rakip Hamlesi
            print(f"\n{opponent.name}'ın Hamlesi (Can: {int(opponent.health)}/{int(opponent.max_health)}, Enerji: {int(opponent.energy)}/{int(opponent.max_energy)})")
            
            opponent_available_abilities = [ab for ab in opponent.active_abilities if ab.current_cooldown == 0 and opponent.energy >= ab.energy_cost]
            if opponent_available_abilities and random.random() > 0.3: 
                selected_ability = random.choice(opponent_available_abilities)
                use_result = selected_ability.use(opponent, self)
                if use_result == "defeated": # Eğer oyuncu yenildiyse
                    print(f"😔 {self.name} savaşı kaybetti!")
                    return "lose"
            else:
                is_crit = random.random() < opponent.crit_chance
                damage = opponent.power * (1.5 if is_crit else 1)
                print(f"🔥 {opponent.name} temel bükme saldırısı yapıyor! {'(KRİTİK VURUŞ!)' if is_crit else ''}")
                if random.random() < self.dodge_chance:
                    print(f"💨 {self.name} saldırıdan kaçtı!")
                else:
                    self.take_damage(damage)

            if self.health <= 0:
                print(f"😔 {self.name} savaşı kaybetti!")
                return "lose"
        
        # Eğer döngü biterse ve kimse ölmediyse (çok nadir olmalı)
        if self.health > 0 and opponent.health > 0 :
             print("Savaş zaman aşımına uğradı ve berabere bitti!")
             return "draw"
        elif self.health > 0 : # Rakip ölmüş olmalı
             print(f"🎉 {self.name} savaşı kazandı (döngü sonu)! 🎉")
             return "win"
        else: # Oyuncu ölmüş olmalı
             print(f"😔 {self.name} savaşı kaybetti (döngü sonu)!")
             return "lose"

    def to_dict(self):
        return {
            "name": self.name,
            "element": self.element.name,
            "bending_style": self.bending_style.name if self.bending_style else None,
            "level": self.level,
            "experience": self.experience,
            "gold": self.gold,
            "reputation": self.reputation,
            "train_count": self.train_count,
            "stat_points": self.stat_points,
            "base_max_health": self.base_max_health,
            "base_power": self.base_power,
            "base_max_energy": self.base_max_energy,
            "max_health": self.max_health,
            "health": self.health,
            "power": self.power,
            "max_energy": self.max_energy,
            "energy": self.energy,
            "crit_chance": self.crit_chance,
            "dodge_chance": self.dodge_chance,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipped_items": [eq.to_dict() for eq in self.equipped_items],
            "abilities": [ability.to_dict() for ability in self.abilities],
            "special_abilities_unlocked": [style.name for style in self.special_abilities_unlocked],
            "buffs": self.buffs, # Buff/Debuff'ları basitçe kaydet, yüklerken özel işlem gerekebilir
            "debuffs": self.debuffs,
            # story_progress gibi özellikler varsa eklenebilir
        }

def choose_bender(name, element, bending_style_str=None): # bending_style_str olarak adlandıralım
    element_upper = element.upper()
    style_arg = bending_style_str.lower() if bending_style_str else None

    if element_upper == "WATER":
        return WaterBender(name, style_arg)
    elif element_upper == "FIRE":
        return FireBender(name, style_arg)
    elif element_upper == "EARTH":
        return EarthBender(name, style_arg)
    elif element_upper == "AIR":
        return AirBender(name, style_arg)
    elif element_upper == "ENERGY":
        return EnergyBender(name) # EnergyBender stil almaz
    else:
        raise ValueError(f"Geçersiz element: {element}")


class WaterBender(Bender):
    def __init__(self, name, bending_style_str=None): # northern, southern vs.
        super().__init__(name, "WATER", bending_style_str)
        self.base_max_health = 120
        self.base_power = 12
        self.base_max_energy = 60
        self.update_stats_from_equipment() # Statları temel değerlere göre güncelle
        # _get_initial_abilities zaten super().__init__ içinde çağrıldı.
        # Sadece bu sınıfa özel ek yetenekler varsa burada learn_ability ile eklenebilir.
        if self.bending_style == BendingStyle.NORTHERN_WATER: # _get_initial_abilities'de olmayanlar
            self.learn_ability(Ability("Buz Mızrağı", "Buzdan keskin bir mızrak fırlatır.", "damage", 25, 12, cooldown=2))
        elif self.bending_style == BendingStyle.SOUTHERN_WATER:
             # Şifa Suyu zaten _get_initial_abilities'de ekleniyor.
             self.learn_ability(Ability("Can Yenilenmesi (Pasif)", "Her turda az miktarda can yenilenir.", "heal", 3, 0, is_active=False))


class FireBender(Bender):
    def __init__(self, name, bending_style_str=None):
        super().__init__(name, "FIRE", bending_style_str)
        self.base_max_health = 100
        self.base_power = 15
        self.base_max_energy = 70
        self.update_stats_from_equipment()
        if self.bending_style == BendingStyle.SUN_WARRIOR_FIRE:
            self.learn_ability(Ability("Güneş Patlaması", "Güneşin gücünü kullanarak hasar verir.", "damage", 28, 14, cooldown=2))
        # Rouge Fire için Alev Patlaması _get_initial_abilities'de ekleniyor.


class EarthBender(Bender):
    def __init__(self, name, bending_style_str=None):
        super().__init__(name, "EARTH", bending_style_str)
        self.base_max_health = 140
        self.base_power = 10
        self.base_max_energy = 40
        self.update_stats_from_equipment()
        if self.bending_style == BendingStyle.SAND_BENDING_EARTH:
            self.learn_ability(Ability("Kum Fırtınası", "Düşmanın isabetini azaltır (güç azaltma olarak).", "debuff_opponent_power", 10, 3, cooldown=3)) # Etki süresi 3 tur
        # Earth Rumble için Taş Kalkan _get_initial_abilities'de ekleniyor

class AirBender(Bender):
    def __init__(self, name, bending_style_str=None):
        super().__init__(name, "AIR", bending_style_str)
        self.base_max_health = 90
        self.base_power = 10 # Temel gücü biraz daha düşük olabilir, hıza odaklı
        self.base_max_energy = 80
        self.crit_chance = 0.10 # Başlangıç kritik ve kaçınma daha yüksek
        self.dodge_chance = 0.15
        self.update_stats_from_equipment()
        if self.bending_style == BendingStyle.AIR_NOMAD_AIR:
            self.learn_ability(Ability("Hava Şoku", "Düşmanı sersemleten güçlü bir hava darbesi.", "debuff_opponent_power", 15, 2, cooldown=3)) # Etki süresi 2 tur
        # Flight için Hızlı Kaçınma _get_initial_abilities'de ekleniyor (crit_buff olarak)
        # Flight için özel pasif Uçuş Hızı:
        elif self.bending_style == BendingStyle.FLIGHT_AIR:
            self.learn_ability(Ability("Uçuş Hızı (Pasif)", "Kalıcı kaçınma şansı artışı.", "dodge_chance_boost", 0.10, 0, is_active=False))


class EnergyBender(Bender):
    def __init__(self, name): # Energy bender stil almaz
        super().__init__(name, "ENERGY") # bending_style None gider
        self.base_max_health = 110
        self.base_power = 13
        self.base_max_energy = 90
        self.update_stats_from_equipment()
        # _get_initial_abilities zaten Enerji Patlaması ekliyor.
        self.learn_ability(Ability("Zihin Bükme", "Düşmanı zihinsel olarak etkiler, gücünü azaltır.", "debuff_opponent_power", 20, 4, cooldown=4)) # Etki süresi 4 tur
        self.learn_ability(Ability("Enerji Toplama", "Enerji yeniler.", "energy", 30, 0, cooldown=3)) # Kullanım limiti yok ama cooldown olabilir.