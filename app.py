import os
from datetime import datetime

# Ініціалізація списку для зберігання рахунку
bill_details = []


def main():
    # Запит номера телефону
    phone_number = input("Введіть номер телефону (без коду країни): ")
    phone_number = "+380" + phone_number
    if not validate_phone_number(phone_number):
        print("Неправильний формат номера телефону. Будь ласка, спробуйте знову.")
        main()
        return

    print("Зробіть вибір комунальних послуг:")
    print("1. Електроенергія")
    print("2. Газ та газопостачання")

    choice = input("Введіть номер послуги (1 або 2): ")

    if choice == '1':
        choose_electricity_tariff()
    elif choice == '2':
        calculate_gas_and_supply()
    else:
        print("Неправильний вибір. Спробуйте ще раз")
        main()

    # Запит на продовження або завершення
    next_action = input("Виберіть: Продовжити (1) або Завершити (2): ")
    if next_action == '1':
        main()
    elif next_action == '2':
        save_bill(phone_number)
    else:
        print("Неправильний вибір. Спробуйте ще раз.")
        main()


def validate_phone_number(phone_number):
    return phone_number.startswith("+380") and len(phone_number) == 13 and phone_number[1:].isdigit()


def choose_electricity_tariff():
    print("\nОберіть тариф на електроенергію:")
    print("1. Однозонний")
    print("2. Двозонний")
    print("3. Трьохзонний")

    tariff_choice = input("Введіть номер тарифу (1, 2 або 3): ")

    if tariff_choice == '1':
        calculate_single_zone_electricity()
    elif tariff_choice == '2':
        calculate_two_zone_electricity()
    elif tariff_choice == '3':
        calculate_three_zone_electricity()
    else:
        print("Неправильний вибір. Спробуйте ще раз.")
        choose_electricity_tariff()


def calculate_single_zone_electricity():
    try:
        current = float(input("Введіть поточні показники (кВт): "))
        previous = float(input("Введіть попередні показники (кВт): "))
        if current < previous:
            print("Помилка: поточні показники повинні бути більшими за попередні.")
            calculate_single_zone_electricity()
            return
        usage = current - previous
        rate = 4.32
        cost = usage * rate
        print(f"Загальна вартість за електроенергію: {cost:.2f} грн")
        bill_details.append(
            f"Електроенергія (Однозонний): {cost:.2f} грн\n"
            f"Поточні показники: {" " * 15} {current}\n"
            f"Попередні показники: {" " * 13} {previous}\n"
            f"Кількість кВт: {" " * 21} {int(current - previous)}\n"
        )
    except ValueError:
        print("Будь ласка, введіть правильні числові значення")
        calculate_single_zone_electricity()


def calculate_two_zone_electricity():
    try:
        current_day = float(input("Введіть поточні показники в зоні День (кВт): "))
        current_night = float(input("Введіть поточні показники в зоні Ніч (кВт): "))
        previous_day = float(input("Введіть попередні показники в зоні День (кВт): "))
        previous_night = float(input("Введіть попередні показники в зоні Ніч (кВт): "))
        if current_day < previous_day or current_night < previous_night:
            print("Помилка: поточні показники повинні бути більшими за попередні.")
            calculate_two_zone_electricity()
            return

        rate_day = 4.32
        rate_night = rate_day * 0.5
        cost_day = (current_day - previous_day) * rate_day
        cost_night = (current_night - previous_night) * rate_night
        total_cost = cost_day + cost_night
        print(f"Загальна вартість за електроенергію (Двозонний тариф): {total_cost:.2f} грн")
        bill_details.append(
            f"Електроенергія (Двозонний):  {total_cost:.2f} грн\n"
            f"\nПоточні показники День: {" " * 10} {int(current_day)}\n"
            f"Поточні показники Ніч: {" " * 11} {int(current_night)}\n"
            f"Попередні показники День: {" " * 8} {int(previous_day)}\n"
            f"Попередні показники Ніч: {" " * 9} {int(previous_night)}\n"
            f"Кількість кВт (День): {" " * 14} {int(current_day - previous_day)}\n"
            f"Кількість кВт (Ніч): {" " * 15} {int(current_night - previous_night)}\n"
        )
    except ValueError:
        print("Будь ласка, введіть правильні числові значення.")
        calculate_two_zone_electricity()


def calculate_three_zone_electricity():
    try:
        current_night = float(input("Введіть поточні показники Ніч (кВт): "))
        current_half_peak = float(input("Введіть поточні показники Напівпік (кВт): "))
        current_peak = float(input("Введіть поточні показники Пік (кВт): "))
        previous_night = float(input("Введіть попередні показники Ніч (кВт): "))
        previous_half_peak = float(input("Введіть попередні показники Напівпік (кВт): "))
        previous_peak = float(input("Введіть попередні показники Пік (кВт): "))
        if current_night < previous_night or current_half_peak < previous_half_peak or current_peak < previous_peak:
            print("Помилка: поточні показники повинні бути більшими за попередні.")
            calculate_three_zone_electricity()
            return

        rate_base = 4.32
        cost_night = (current_night - previous_night) * rate_base * 0.4
        cost_half_peak = (current_half_peak - previous_half_peak) * rate_base
        cost_peak = (current_peak - previous_peak) * rate_base * 1.5
        total_cost = cost_night + cost_half_peak + cost_peak
        print(f"Загальна вартість за електроенергію (Трьохзонний тариф): {total_cost:.2f} грн")
        bill_details.append(
            f"Електроенергія (Трьохзонний): {total_cost:.2f}грн\n"
            f"\nПоточні показники Ніч: {" " * 11} {int(current_night)}\n"
            f"Поточні показники Напівпік: {" " * 6} {int(current_half_peak)}\n"
            f"Поточні показники Пік: {" " * 11} {int(current_peak)}\n"
            f"Попередні показники Ніч: {int(previous_night)}\n"
            f"Попередні показники Напівпік: {" " * 4} {int(previous_half_peak)}\n"
            f"Попередні показники Пік: {" " * 9} {int(previous_peak)}\n"
            f"Кількість кВт при Нічному тарифі:    {int(current_night - previous_night)}\n"
            f"Кількість кВт при Напівпік тарифі:   {int(current_half_peak - previous_half_peak)}\n"
            f"Кількість кВт при Пік тарифі: {" " * 6} {int(current_peak - previous_peak)}\n"
        )
    except ValueError:
        print("Будь ласка, введіть правильні числові значення.")
        calculate_three_zone_electricity()


def calculate_gas_and_supply():
    try:
        current = float(input("Введіть поточні показники (м³): "))
        previous = float(input("Введіть попередні показники (м³): "))
        if current < previous:
            print("Помилка: поточні показники повинні бути більшими за попередні.")
            calculate_gas_and_supply()
            return

        usage = current - previous
        cost_gas = usage * 7.96
        cost_supply = usage * 1.308
        total_cost = cost_gas + cost_supply

        print(f"Загальна вартість за газ: {cost_gas:.2f} грн")
        print(f"Загальна вартість за газопостачання: {cost_supply:.2f} грн")
        print(f"Загальна сума: {total_cost:.2f} грн")

        bill_details.append(
            f"Газ: {" " * 23} {cost_gas:.2f} грн\n"
            f"\nПоточні показники: {" " * 16} {int(current)}\n"
            f"Попередні показники: {" " * 14} {int(previous)}\n"
            f"\nСпожито: {" " * 22} {usage:.2f} м3\n"
            )
        
        bill_details.append(
            f"Газопостачання: {" " * 13} {cost_supply:.2f} грн\n"
            f"Об'єм тарнспортування: {" " * 8} {usage:.2f} м3\n"
        )
    except ValueError:
        print("Будь ласка, введіть правильні числові значення.")
        calculate_gas_and_supply()


def save_bill(phone_number):
    # Створення папки Archive, якщо її ще немає
    if not os.path.exists("Archive"):
        os.makedirs("Archive")

    # Створення файлу з рахунком
    file_path = f"Archive/bill_{phone_number[4:]}.txt"
    with open(file_path, "a") as file:
        # Дата і час
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"\n---- Рахунок від {timestamp} ----\n")
        file.write(f"\nРахунок для телефону: {" " * 5} {phone_number}\n")
        file.write("\n" + " " * 13 + "Деталі рахунку:\n")
        for item in bill_details:
            file.write(f"{item}\n")
        file.write("Дякуємо за користування нашими послугами!")
        file.write("\n" + "-" * 41 + "\n")

    print(f"Рахунок збережено у файлі: {file_path}")


if __name__ == "__main__":
    main()
