import random
from benders import (WaterBender, FireBender, EarthBender, 
                    AirBender, EnergyBender, Element, BendingStyle,
                    choose_bender)
from data import (save_bender_data, load_bender_list_names, 
                 load_bender_data, get_leaderboard)
from game import (create_character_interactive, show_status,
                 initiate_battle, StoryManager, shop_menu, inventory_menu,
                 manage_quests, train_character_action, choose_player_character,
                 explore_dungeon, # special_event_chance, # Bu bir integer, fonksiyon değil
                 random_city_event,
                 visit_elemental_temple, QUESTS, main_game_loop as game_main_loop) # game.py'deki ana döngüyü de alabiliriz

created_benders = [] 
current_bender = None 
story_manager = StoryManager() # game.py içindeki StoryManager'ı kullanır

def load_characters_to_list():
    global created_benders
    names = load_bender_list_names()
    loaded_benders = []
    for name in names:
        bender = load_bender_data(name)
        if bender:
            loaded_benders.append(bender)
    created_benders = loaded_benders
    if created_benders:
        print(f"{len(created_benders)} karakter yüklendi.")
    else:
        print("Kayıtlı karakter bulunamadı veya yüklenemedi.")


def save_all_characters():
    if not created_benders:
        print("Kaydedilecek aktif karakter yok.")
        return
    for bender in created_benders:
        if bender: # None kontrolü
            save_bender_data(bender)
    print("Tüm aktif karakterler kaydedildi.")


def character_operations_menu(): # current_bender'ı global olarak kullanacak
    global current_bender
    if not created_benders:
        print("\nHenüz karakter oluşturulmadı veya yüklü karakter yok.")
        return

    if not current_bender: # Eğer aktif bir bender seçilmemişse, seçtir
        print("Önce işlem yapılacak bir karakter seçmelisiniz.")
        current_bender = choose_player_character(created_benders, "İşlem yapmak istediğiniz karakteri seçin:")
        if not current_bender:
            return # Seçim yapılmadıysa geri dön

    print(f"\nAktif Karakter: {current_bender.name}")
    while True:
        print(f"\n=== {current_bender.name} İşlemleri ===")
        print("1. Durumu Gör")
        print("2. Karakter Eğit")
        print("3. Envanter & Ekipman")
        print("4. Görevleri Yönet")
        print("5. Stat Puanı Dağıt (game.py'den)") # game.py'deki fonksiyonu kullanabiliriz
        print("0. Ana Menüye Dön")

        choice = input("Seçiminiz: ")

        if choice == "1":
            show_status(current_bender)
        elif choice == "2":
            train_character_action(current_bender) # game.py'den
            save_bender_data(current_bender) # Her işlem sonrası kaydet
            # random_city_event(current_bender) # game.py'den, isteğe bağlı
        elif choice == "3":
            inventory_menu(current_bender) # game.py'den
            save_bender_data(current_bender)
        elif choice == "4":
            manage_quests(current_bender) # game.py'den
            save_bender_data(current_bender)
        elif choice == "5":
            from game import distribute_stat_points # game.py'den import et
            distribute_stat_points(current_bender)
            save_bender_data(current_bender)
        elif choice == "0":
            break
        else:
            print("❌ Geçersiz seçim. Lütfen geçerli bir sayı girin.")
        
        # İsteğe bağlı: Her işlem sonrası özel olaylar
        # if random.randint(1, 100) <= game.special_event_chance: # game.py'deki değişkeni kullan
        #    print("Bir şeyler oldu!") # Ya da random_city_event çağırılabilir

def show_leaderboard():
    print("\n=== LİDERLİK TABLOSU 🏆 ===")
    leaderboard = get_leaderboard()
    if not leaderboard:
        print("Liderlik tablosu boş.")
        return

    print(f"{'Sıra':<5} {'Ad':<20} {'Seviye':<10} {'Güç':<10} {'İtibar':<10} {'Element':<15}")
    print("-" * 75)
    for i, (name, level, power, reputation, element) in enumerate(leaderboard, 1):
        element_display = element.replace("_", " ").title() # Element adını güzelleştir
        print(f"{i:<5} {name:<20} {level:<10} {int(power):<10} {reputation:<10} {element_display:<15}")


def main_menu():
    global current_bender, created_benders
    load_characters_to_list() 

    while True:
        print("\n=== ANA MENÜ 🎮 ===")
        if current_bender:
            print(f"Aktif Karakter: {current_bender.name} (Seviye: {current_bender.level})")
        else:
            print("Aktif Karakter: Yok")

        print("1. Yeni Karakter Oluştur")
        print("2. Karakter Seç / Değiştir")
        print("3. Karakter İşlemleri (Aktif karakter ile)")
        print("4. Savaş!")
        print("5. Dükkan")
        print("6. Keşfet / Konum Değiştir") # game.py'deki explore_location'ı kullanır
        print("7. Hikaye İlerlemesi (Aktif karakter için)")
        print("8. Liderlik Tablosu")
        print("9. Tüm Karakterleri Kaydet")
        print("0. Çıkış (Değişiklikler Kaydedilmez, 9 ile kaydedin)")

        choice = input("Seçiminiz: ")

        if choice == "1":
            new_char = create_character_interactive() # game.py'den
            if new_char:
                # Aynı isimde karakter var mı kontrol et (opsiyonel)
                is_new = True
                for i, b in enumerate(created_benders):
                    if b.name == new_char.name:
                        created_benders[i] = new_char # Eskisini güncelle
                        is_new = False
                        break
                if is_new:
                    created_benders.append(new_char)
                
                current_bender = new_char
                save_bender_data(current_bender)
                print(f"'{current_bender.name}' aktif karakter olarak ayarlandı.")
        
        elif choice == "2":
            if not created_benders:
                print("Önce karakter oluşturun veya yükleyin.")
                continue
            chosen_one = choose_player_character(created_benders, "Aktif olacak karakteri seçin:")
            if chosen_one:
                current_bender = chosen_one
                print(f"'{current_bender.name}' aktif karakter olarak ayarlandı.")
        
        elif choice == "3":
            if not current_bender:
                print("Önce bir karakter seçmelisiniz (Seçenek 2).")
                continue
            character_operations_menu() # Bu fonksiyon global current_bender'ı kullanır

        elif choice == "4":
            if not current_bender:
                print("Savaşmak için önce bir karakter seçin (Seçenek 2).")
                continue
            # initiate_battle tüm bender listesini değil, aktif bender'ı ve diğerlerini yönetmeli.
            # game.py'deki initiate_battle(benders) listeyi alır ve içinden seçtirir.
            # Eğer sadece aktif bender vs NPC olacaksa:
            # player_for_battle = current_bender
            # initiate_battle([player_for_battle]) # game.py'deki fonksiyonu çağır
            # Ya da game.py'deki gibi tüm listeyi verip seçtirsin:
            initiate_battle(created_benders) # game.py'deki fonksiyon
            if current_bender: save_bender_data(current_bender) # Savaş sonrası aktif karakteri kaydet

        elif choice == "5":
            if not current_bender:
                print("Dükkanı kullanmak için önce bir karakter seçin (Seçenek 2).")
                continue
            shop_menu(current_bender) # game.py'den
            save_bender_data(current_bender) 

        elif choice == "6": # Keşfet / Konum Değiştir
            if not current_bender:
                print("Keşfetmek için önce bir karakter seçin (Seçenek 2).")
                continue
            from game import game_map, explore_location # game.py'den harita ve keşif fonksiyonu
            # game.py içinde bir game_map örneği olmalı veya burada oluşturulmalı
            # Şimdilik game.py'de global bir game_map olduğunu varsayalım
            # Eğer yoksa: game_map_instance = game.Map() 
            # explore_location(current_bender, game_map_instance)
            # Bu menü game.py'nin ana döngüsündeki gibi daha detaylı olmalı
            print("Bu özellik için game.py'deki ana oyun döngüsüne (Menü Seçenek 9) bakınız.")
            print("Şimdilik basit bir explore_dungeon çağrısı yapılıyor (varsa):")
            try:
                 explore_dungeon(current_bender) # Eğer explore_dungeon direkt zindan ise
                 save_bender_data(current_bender)
            except NameError: # Eğer explore_dungeon yoksa
                 print("explore_dungeon fonksiyonu bulunamadı.")
            # Daha iyisi: game.py'deki explore_location çağrılmalı.
            # game.py içindeki main_game_loop'un ilgili kısmını buraya entegre etmek gerekebilir.

        elif choice == "7":
            if not current_bender:
                print("Hikaye ilerlemesini görmek için önce bir karakter seçin (Seçenek 2).")
                continue
            story_manager.show_story_progress(current_bender.name) # game.py'den

        elif choice == "8":
            show_leaderboard()

        elif choice == "9":
            save_all_characters()
            
        elif choice == "0":
            print("👋 Oyundan çıkılıyor... Hoşça kalın! 👋")
            break
        else:
            print("❌ Geçersiz seçim. Lütfen geçerli bir sayı girin.")

if __name__ == "__main__":
    # game_main_loop() # Eğer game.py'deki ana döngüyü direkt kullanmak isterseniz
    main_menu() # Ya da bu dosyadaki main_menu'yü kullanın