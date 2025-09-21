
# Muhasebe & Finans Hesap Makinesi
# Modüler, Flet tabanlı masaüstü uygulama
# Her modül ve fonksiyon için açıklayıcı yorumlar eklendi

from __future__ import annotations
import flet as ft
from decimal import Decimal, getcontext, ROUND_HALF_UP
from dataclasses import dataclass
from typing import List, Tuple


# Decimal ayarları: Finansal hassasiyet için
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP
Decimal0 = Decimal("0")


# String veya sayıdan Decimal'a güvenli dönüşüm
def D(x):
    try:
        return Decimal(str(x).replace(",", ".").strip())
    except Exception:
        return Decimal0


# Decimal'ı Türkçe formatta stringe çevirir
def fmt(x: Decimal, nd=2) -> str:
    q = Decimal(10) ** -nd
    return f"{x.quantize(q):,}".replace(",", "_").replace(".", ",").replace("_", ".")


# KDV Hesaplama modülü
def KDVTab():
    mode = ft.Dropdown(
        label="Hesap Türü",
        options=[ft.dropdown.Option("KDV Hariç → KDV Dahil"), ft.dropdown.Option("KDV Dahil → KDV Hariç (Ters KDV)")],
        value="KDV Hariç → KDV Dahil",
    icon="swap_horiz",
        width=320
    )
    tutar = ft.TextField(label="Tutar (TL)", value="1000", hint_text="Örn: 1000", prefix_icon="attach_money", width=200)
    kdv_oran = ft.TextField(label="KDV %", value="20", hint_text="Örn: 20", prefix_icon="percent", width=120)
    sonuc = ft.Text(value="", selectable=True)

    # KDV hesaplama fonksiyonu
    def hesapla(e):
        t, o = D(tutar.value), D(kdv_oran.value)/Decimal(100)
        if mode.value == "KDV Hariç → KDV Dahil":
            kdv = t*o
            toplam = t+kdv
            sonuc.value = f"KDV: {fmt(kdv)} TL\nToplam (Dahil): {fmt(toplam)} TL"
        elif mode.value == "KDV Dahil → KDV Hariç (Ters KDV)":
            net = t/(Decimal(1)+o) if o!=Decimal0 else t
            kdv = t-net
            sonuc.value = f"Net (Hariç): {fmt(net)} TL\nKDV: {fmt(kdv)} TL"
        else:
            sonuc.value = "Hatalı mod seçimi!"
        sonuc.update()

    # Modülün ana arayüzü
    return ft.Container(
        content=ft.Column([
            ft.Text("KDV Hesaplayıcı", weight=ft.FontWeight.BOLD, color="#0D47A1", size=20),
            mode,
            ft.Row([tutar, kdv_oran, ft.ElevatedButton("Hesapla", icon="calculate", on_click=hesapla)], spacing=10),
            ft.Divider(),
            sonuc,
        ], spacing=12),
        bgcolor="#E3F2FD",
        padding=16,
        expand=True
    )


# Kredi ödeme planı için bir dönemlik satır
@dataclass
class ScheduleItem:
    period: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal

    # Anüite (eşit taksitli) kredi ödeme formülü
def annuity_payment(principal: Decimal, annual_rate_pct: Decimal, months: int) -> Decimal:
    r = (annual_rate_pct/Decimal(100))/Decimal(12)
    if r == Decimal0:
        return principal/Decimal(months)
    denom = (Decimal(1) - (Decimal(1)+r) ** Decimal(-months))
    return principal * r / denom

    # Kredi ödeme planı tablosu oluşturur
def build_schedule(P: Decimal, rate_pct: Decimal, n: int) -> List[ScheduleItem]:
    pay = annuity_payment(P, rate_pct, n)
    bal = P
    out: List[ScheduleItem] = []
    r = (rate_pct/Decimal(100))/Decimal(12)
    for t in range(1, n+1):
        interest = bal*r
        principal = pay - interest
        bal = bal - principal
        if bal < Decimal("0.00001"): bal = Decimal0
        out.append(ScheduleItem(t, pay, interest, principal, bal))
    return out

    # Kredi ödeme planı modülü
def CreditTab():
    principal = ft.TextField(label="Anapara (TL)", value="100000", hint_text="Örn: 100000", prefix_icon="attach_money", width=200)
    rate = ft.TextField(label="Yıllık Faiz %", value="36", hint_text="Örn: 36", prefix_icon="percent", width=160)
    months = ft.TextField(label="Vade (ay)", value="24", hint_text="Örn: 24", prefix_icon="date_range", width=120)
    out = ft.Text(value="")
    table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Dönem")),
        ft.DataColumn(ft.Text("Taksit")),
        ft.DataColumn(ft.Text("Faiz")),
        ft.DataColumn(ft.Text("Anapara")),
        ft.DataColumn(ft.Text("Bakiye")),
    ], rows=[], width=800)
    csv_path = ft.TextField(label="CSV Kaydet (yol/adi.csv)", hint_text="Örn: odeme.csv", prefix_icon="save", width=320)

    # Hesaplama ve tabloyu doldurma fonksiyonu
    def calc(e):
        P, r, n = D(principal.value), D(rate.value), int(D(months.value))
        sched = build_schedule(P, r, n)
        total_pay = sum((it.payment for it in sched), Decimal0)
        total_int = sum((it.interest for it in sched), Decimal0)
        out.value = f"Aylık Taksit: {fmt(sched[0].payment)} TL | Toplam Ödeme: {fmt(total_pay)} TL | Toplam Faiz: {fmt(total_int)} TL"
        table.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(it.period))), ft.DataCell(ft.Text(fmt(it.payment))), ft.DataCell(ft.Text(fmt(it.interest))), ft.DataCell(ft.Text(fmt(it.principal))), ft.DataCell(ft.Text(fmt(it.balance)))]) for it in sched]
        out.update()
        table.update()

    # Tabloyu CSV olarak kaydetme fonksiyonu
    def save_csv(e):
        import csv
        path = (csv_path.value or "odeme_plani.csv").strip()
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Donem", "Taksit", "Faiz", "Anapara", "Bakiye"])
            for r in table.rows:
                vals = [c.content.value for c in r.cells]
                w.writerow(vals)

    # Modülün ana arayüzü
    return ft.Container(
        content=ft.Column([
            ft.Text("Kredi Ödeme Planı (Anüite)", weight=ft.FontWeight.BOLD, color="#1B5E20", size=20),
            ft.Row([principal, rate, months, ft.ElevatedButton("Planı Oluştur", icon="calculate", on_click=calc)], spacing=10),
            out,
            ft.Container(table, bgcolor="#C8E6C9", padding=10),
            ft.Row([csv_path, ft.OutlinedButton("CSV Olarak Kaydet", icon="save", on_click=save_csv)], spacing=10),
        ], spacing=12, scroll=ft.ScrollMode.ADAPTIVE),
        bgcolor="#E8F5E9",
        padding=16,
        expand=True
    )

    # Amortisman hesaplama modülü
def DepTab():
    cost = ft.TextField(label="Maliyet (TL)", value="50000", hint_text="Örn: 50000", prefix_icon="work", width=180)
    salv = ft.TextField(label="Hurda Değer (TL)", value="0", hint_text="Örn: 0", prefix_icon="remove", width=160)
    life = ft.TextField(label="Ekonomik Ömür (yıl)", value="5", hint_text="Örn: 5", prefix_icon="calendar_month", width=170)
    method = ft.Dropdown(label="Yöntem", options=[ft.dropdown.Option("Normal"), ft.dropdown.Option("Azalan Bakiye")], value="Normal", icon="swap_vert", width=180)
    table = ft.DataTable(columns=[ft.DataColumn(ft.Text("Yıl")), ft.DataColumn(ft.Text("Amortisman")), ft.DataColumn(ft.Text("Birikmiş")), ft.DataColumn(ft.Text("Net Defter Değeri"))], rows=[], width=700)

    # Hesaplama ve tabloyu doldurma fonksiyonu
    def calc(e):
        c, s, l = D(cost.value), D(salv.value), int(D(life.value))
        rows = []
        acc = Decimal0
        nbv = c
        if method.value == "Normal":
            dep = (c - s) / Decimal(l)
            for y in range(1, l + 1):
                acc += dep
                nbv = c - acc
                rows.append((y, dep, acc, max(nbv, s)))
        else:
            rate = (Decimal(2) / Decimal(l))
            for y in range(1, l + 1):
                dep = (nbv * rate)
                if y == l and nbv - dep < s:
                    dep = nbv - s
                acc += dep
                nbv -= dep
                rows.append((y, dep, acc, nbv))
        table.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(y))), ft.DataCell(ft.Text(fmt(dep))), ft.DataCell(ft.Text(fmt(acc))), ft.DataCell(ft.Text(fmt(nbv)))]) for (y, dep, acc, nbv) in rows]
        table.update()

    # Modülün ana arayüzü
    return ft.Container(
        content=ft.Column([
            ft.Text("Amortisman Hesabı", weight=ft.FontWeight.BOLD, color="#212121", size=20),
            ft.Row([cost, salv, life, method, ft.ElevatedButton("Hesapla", icon="calculate", on_click=calc)], spacing=10),
            ft.Container(table, bgcolor="#F5F5F5", padding=10),
        ], spacing=12),
        bgcolor="#EEEEEE",
        padding=16,
        expand=True
    )

    # Stok maliyetleme modülü
def InventoryTab():
    input_field = ft.TextField(label="İşlemler (satır satır)", multiline=True, min_lines=8, max_lines=14, value="ALIS;100;10\nALIS;50;12\nSATIS;120;0", hint_text="ALIS;100;10", prefix_icon="list", width=500)
    method = ft.Dropdown(label="Yöntem", options=[ft.dropdown.Option("FIFO"), ft.dropdown.Option("LIFO"), ft.dropdown.Option("Ağırlıklı Ortalama")], value="FIFO", icon="swap_horiz", width=220)
    out = ft.Text(value="", selectable=True)
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("İşlem")),
            ft.DataColumn(ft.Text("Miktar")),
            ft.DataColumn(ft.Text("Birim Maliyet")),
        ],
        rows=[],
        width=500
    )

    # Kullanıcıdan girilen işlemleri satır satır ayrıştırır
    def parse_lines():
        rows = []
        val = input_field.value if input_field.value is not None else ""
        for line in val.splitlines():
            if not line.strip():
                continue
            parts = [p.strip().upper() for p in line.split(";")]
            if len(parts) < 3: continue
            typ, qty, price = parts[0], D(parts[1]), D(parts[2])
            rows.append((typ, qty, price))
        return rows

    # Stok hesaplama ve tabloyu doldurma fonksiyonu
    def calc(e):
        ops = parse_lines()
        cogs_total = Decimal0
        inventory: List[Tuple[Decimal, Decimal]] = []  # (qty, unit_cost)
        avg_cost = Decimal0
        # Tabloyu doldur
        table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(typ))),
                ft.DataCell(ft.Text(fmt(qty, 2))),
                ft.DataCell(ft.Text(fmt(price, 2)))
            ]) for typ, qty, price in ops
        ]
        # ...stok hesaplama...
        for typ, qty, price in ops:
            if typ == "ALIS":
                if method.value == "Ağırlıklı Ortalama":
                    total_qty = sum((q for q, _ in inventory), Decimal0) + qty
                    total_cost = sum((q*c for q, c in inventory), Decimal0) + qty*price
                    avg_cost = (total_cost / total_qty) if total_qty != Decimal0 else Decimal0
                    inventory = [(total_qty, avg_cost)]
                else:
                    inventory.append((qty, price))
            elif typ == "SATIS":
                remaining = qty
                if method.value == "FIFO":
                    inv_order = list(inventory)
                elif method.value == "LIFO":
                    inv_order = list(reversed(inventory))
                else:  # Avg
                    inv_order = list(inventory)
                new_layers: List[Tuple[Decimal, Decimal]] = []
                for q, c in inv_order:
                    if remaining <= Decimal0: break
                    use = min(q, remaining)
                    cogs_total += use * (avg_cost if method.value=="Ağırlıklı Ortalama" else c)
                    q_left = q - use
                    remaining -= use
                    if q_left > Decimal0:
                        new_layers.append((q_left, c))
                if method.value == "FIFO":
                    inventory = new_layers + inv_order[len(new_layers):]
                elif method.value == "LIFO":
                    original = list(inventory)
                    total_qty = sum(q for q, _ in original) - qty
                    inv_qty_cost: List[Tuple[Decimal, Decimal]] = []
                    rem = total_qty
                    for q, c in original:
                        if rem <= Decimal0: break
                        use = min(q, rem)
                        inv_qty_cost.append((use, c))
                        rem -= use
                    inventory = inv_qty_cost
                else:  # Avg
                    curr_qty = inventory[0][0] if inventory else Decimal0
                    inventory = [(max(curr_qty - qty, Decimal0), avg_cost)]
        end_qty = sum((q for q, _ in inventory), Decimal0)
        end_cost = sum((q*c for q, c in inventory), Decimal0)
        out.value = f"Satılan Malın Maliyeti (COGS): {fmt(cogs_total)} TL\nDönem Sonu Stok: {fmt(end_qty)} birim | Değer: {fmt(end_cost)} TL"
        out.update()
        table.update()

    # Modülün ana arayüzü
    return ft.Container(
        content=ft.Column([
            ft.Text("Stok Maliyetleme", weight=ft.FontWeight.BOLD, color="#E65100", size=20),
            ft.Row([method, ft.ElevatedButton("Hesapla", icon="calculate", on_click=calc)], spacing=10),
            input_field,
            ft.Divider(),
            table,
            out,
        ], spacing=12, scroll=ft.ScrollMode.ADAPTIVE),
        bgcolor="#FFF3E0",
        padding=16,
        expand=True
    )

    # Kırılma noktası (BEP) hesaplama modülü
def BEPTab():
    price = ft.TextField(label="Birim Satış Fiyatı", value="50", hint_text="Örn: 50", prefix_icon="sell", width=180)
    varc = ft.TextField(label="Birim Değişken Maliyet", value="30", hint_text="Örn: 30", prefix_icon="money_off", width=210)
    fixed = ft.TextField(label="Sabit Giderler (TL)", value="20000", hint_text="Örn: 20000", prefix_icon="business", width=210)
    target_profit = ft.TextField(label="Hedef Kâr (opsiyonel)", value="0", hint_text="Örn: 5000", prefix_icon="star", width=180)
    out = ft.Text(value="")

    # Hesaplama fonksiyonu
    def calc(e):
        p, v, F, TP = D(price.value), D(varc.value), D(fixed.value), D(target_profit.value)
        cm = p - v
        units = (F / cm) if cm != Decimal0 else Decimal0
        rev = units * p
        units_tp = (F + TP) / cm if cm != Decimal0 else Decimal0
        out.value = f"BEP (Birim): {fmt(units, 2)} | BEP (Ciro): {fmt(rev, 2)} TL\nHedef Kâr için Gerekli Satış (Birim): {fmt(units_tp, 2)}"
        out.update()

    # Modülün ana arayüzü
    return ft.Container(
        content=ft.Column([
            ft.Text("Kırılma Noktası (BEP)", weight=ft.FontWeight.BOLD, color="#4A148C", size=20),
            ft.Row([price, varc, fixed, target_profit, ft.ElevatedButton("Hesapla", icon="calculate", on_click=calc)], spacing=10),
            ft.Divider(),
            out,
        ], spacing=12),
        bgcolor="#F3E5F5",
        padding=16,
        expand=True
    )

    # Basit bordro (brüt→net) hesaplama modülü
def PayrollTab():
    gross = ft.TextField(label="Brüt Ücret (TL)", value="30000", hint_text="Örn: 30000", prefix_icon="payments", width=200)
    sgk = ft.TextField(label="SGK İşçi %", value="14", hint_text="Örn: 14", prefix_icon="health_and_safety", width=140)
    income_tax = ft.TextField(label="Gelir Vergisi %", value="15", hint_text="Örn: 15", prefix_icon="percent", width=140)
    stamp_tax = ft.TextField(label="Damga Vergisi %", value="0.759", hint_text="Örn: 0.759", prefix_icon="money", width=160)
    out = ft.Text(value="")

    # Hesaplama fonksiyonu
    def calc(e):
        G = D(gross.value)
        sgk_v = D(sgk.value) / Decimal(100)
        gv = D(income_tax.value) / Decimal(100)
        dv = D(stamp_tax.value) / Decimal(100)
        sgk_tutar = G * sgk_v
        vergi_matrah = G - sgk_tutar
        gelir_vergisi = vergi_matrah * gv
        damga = G * dv
        net = G - sgk_tutar - gelir_vergisi - damga
        out.value = f"SGK Tutarı: {fmt(sgk_tutar)} TL\nGelir Vergisi: {fmt(gelir_vergisi)} TL\nDamga Vergisi: {fmt(damga)} TL\nNet Ücret: {fmt(net)} TL"
        out.update()

    # Modülün ana arayüzü
    return ft.Container(
        content=ft.Column([
            ft.Text("Basit Bordro (Brüt→Net) – Eğitim Amaçlı", weight=ft.FontWeight.BOLD, color="#B71C1C", size=20),
            ft.Row([gross, sgk, income_tax, stamp_tax, ft.ElevatedButton("Hesapla", icon="calculate", on_click=calc)], spacing=10),
            ft.Divider(),
            out,
        ], spacing=12),
        bgcolor="#FFEBEE",
        padding=16,
        expand=True
    )

    # Uygulamanın ana fonksiyonu, tüm modülleri ve arayüzü oluşturur
def main(page: ft.Page):
    page.title = "Muhasebe & Finans Hesap Makinesi"
    tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="KDV", content=KDVTab()),
            ft.Tab(text="Kredi Planı", content=CreditTab()),
            ft.Tab(text="Amortisman", content=DepTab()),
            ft.Tab(text="Stok", content=InventoryTab()),
            ft.Tab(text="BEP", content=BEPTab()),
            ft.Tab(text="Bordro", content=PayrollTab()),
        ],
        expand=1
    )
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Muhasebe Modülleri", size=18, weight=ft.FontWeight.BOLD, color="#212121"),
                ft.Divider(),
                tabs
            ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.alignment.center,
            padding=0,
        )
    )
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE


# Uygulama giriş noktası
if __name__ == "__main__":
    ft.app(target=main)
