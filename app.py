import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

# PAGE CONFIG
st.set_page_config(
    page_title="E-Commerce Analysis Dashboard",
    layout="wide"
)

st.title("📦 E-Commerce Public Dataset Dashboard")
st.caption("Ringkasan hasil Exploratory Data Analysis (EDA)")

# LOAD DATA
@st.cache_data
def load_data():
    orders = pd.read_csv("data/olist_orders_dataset.csv")
    order_items = pd.read_csv("data/olist_order_items_dataset.csv")
    products = pd.read_csv("data/olist_products_dataset.csv")
    customers = pd.read_csv("data/olist_customers_dataset.csv")
    sellers = pd.read_csv("data/olist_sellers_dataset.csv")
    order_reviews = pd.read_csv("data/olist_order_reviews_dataset.csv")

    # datetime conversion (sesuai cleaning)
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    orders["order_delivered_customer_date"] = pd.to_datetime(
        orders["order_delivered_customer_date"], errors="coerce"
    )
    orders["order_estimated_delivery_date"] = pd.to_datetime(
        orders["order_estimated_delivery_date"], errors="coerce"
    )

    return orders, order_items, products, customers, sellers, order_reviews


orders, order_items, products, customers, sellers, order_reviews = load_data()

# PREPARE DATA
orders_delivery = orders[orders["order_delivered_customer_date"].notna()].copy()

orders_delivery["delivery_time"] = (
    orders_delivery["order_delivered_customer_date"]
    - orders_delivery["order_purchase_timestamp"]
).dt.days

orders_delivery["is_delayed"] = (
    orders_delivery["order_delivered_customer_date"]
    > orders_delivery["order_estimated_delivery_date"]
)

# KPI SECTION
st.markdown("### 📊 Ringkasan Utama")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Order", f"{orders.shape[0]:,}")

with col2:
    st.metric(
        "Persentase Keterlambatan",
        f"{orders_delivery['is_delayed'].mean() * 100:.2f}%"
    )

with col3:
    st.metric(
        "Rata-rata Review Score",
        f"{order_reviews['review_score'].mean():.2f}"
    )

st.markdown("---")

# PERTANYAAN 1
st.subheader("📉 Kategori Produk dengan Penjualan Terendah")

items_products = order_items.merge(
    products[["product_id", "product_category_name"]],
    on="product_id",
    how="left"
)

low_sales_categories = (
    items_products
    .groupby("product_category_name")
    .size()
    .reset_index(name="total_sales")
    .sort_values("total_sales")
    .head(10)
)

fig1, ax1 = plt.subplots(figsize=(8, 6))
sns.barplot(
    data=low_sales_categories,
    x="total_sales",
    y="product_category_name",
    hue="product_category_name",
    palette="flare",
    legend=False,
    ax=ax1
)
ax1.set_xlabel("Total Penjualan")
ax1.set_ylabel(None)
ax1.set_yticklabels(ax1.get_yticklabels(), style="italic")
sns.despine()
st.pyplot(fig1)

st.markdown(
    "Beberapa kategori produk memiliki volume penjualan yang sangat rendah dibandingkan kategori lainnya. "
    "Kategori seperti *seguros_e_servicos*, *fashion_roupa_infanto_juvenil*, dan *pc_gamer* berada pada tingkat "
    "penjualan terendah, yang mengindikasikan adanya perbedaan permintaan yang cukup signifikan antar kategori "
    "produk di platform."
)

st.markdown("---")

# PERTANYAAN 2
st.subheader("🏬 Negara Bagian dengan Jumlah Seller Tertinggi")

top_seller_states = (
    sellers
    .groupby("seller_state")
    .seller_id.nunique()
    .reset_index(name="total_sellers")
    .sort_values("total_sellers", ascending=False)
    .head(10)
)

fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.barplot(
    data=top_seller_states,
    x="total_sellers",
    y="seller_state",
    hue="seller_state",
    palette="flare",
    legend=False,
    ax=ax2
)
ax2.set_xlabel("Jumlah Seller")
ax2.set_ylabel("State")
sns.despine()
st.pyplot(fig2)

st.markdown(
    "Distribusi seller sangat tidak merata antar negara bagian. SP (São Paulo) mendominasi jumlah seller dengan "
    "selisih yang jauh dibandingkan state lain seperti PR (Paraná) dan MG (Minas Gerais), sementara sebagian besar "
    "state lainnya hanya memiliki jumlah seller yang relatif kecil. Temuan ini mengindikasikan adanya konsentrasi "
    "aktivitas penjual yang kuat pada wilayah tertentu di platform."
)

st.markdown("---")

# PERTANYAAN 3
st.subheader("🚚 Dampak Keterlambatan terhadap Skor Ulasan")

delivery_reviews = orders_delivery.merge(
    order_reviews[["order_id", "review_score"]],
    on="order_id",
    how="inner"
)

delay_review_summary = (
    delivery_reviews
    .groupby("is_delayed")
    .review_score.mean()
    .reset_index()
)

delay_review_summary["status"] = delay_review_summary["is_delayed"].map(
    {False: "Tepat Waktu", True: "Terlambat"}
)

fig3, ax3 = plt.subplots(figsize=(6, 4))
sns.barplot(
    data=delay_review_summary,
    x="review_score",
    y="status",
    hue="status",
    palette=["#008450", "#B81D13"],
    legend=False,
    ax=ax3
)
ax3.set_xlabel("Rata-rata Review Score")
ax3.set_ylabel(None)
sns.despine()
st.pyplot(fig3)

st.markdown(
    "Terdapat perbedaan yang jelas pada rata-rata skor ulasan antara pesanan yang dikirim tepat waktu dan yang "
    "mengalami keterlambatan. Pesanan tepat waktu memiliki rata-rata skor ulasan yang jauh lebih tinggi dibandingkan "
    "pesanan terlambat, yang mengindikasikan bahwa keterlambatan pengiriman berkaitan dengan penurunan tingkat kepuasan pelanggan."
)

st.markdown("---")

# PERTANYAAN 4
st.subheader("📍 State dengan Rasio Keterlambatan Tertinggi")

delivery_state = orders_delivery.merge(
    customers[["customer_id", "customer_state"]],
    on="customer_id",
    how="inner"
)

state_delay = (
    delivery_state
    .groupby("customer_state")
    .agg(
        total_orders=("order_id", "count"),
        delayed_orders=("is_delayed", "sum")
    )
    .reset_index()
)

state_delay["delay_ratio"] = (
    state_delay["delayed_orders"] / state_delay["total_orders"]
)

top_states_delay = (
    state_delay
    .sort_values("total_orders", ascending=False)
    .head(10)
    .sort_values("delay_ratio", ascending=False)
)

fig4, ax4 = plt.subplots(figsize=(8, 6))
sns.barplot(
    data=top_states_delay,
    x="delay_ratio",
    y="customer_state",
    hue="customer_state",
    palette="flare",
    legend=False,
    ax=ax4
)
ax4.set_xlabel("Rasio Keterlambatan")
ax4.set_ylabel("State")
sns.despine()
st.pyplot(fig4)

st.markdown(
    "Rasio keterlambatan pengiriman bervariasi cukup signifikan antar negara bagian. BA (Bahia), RJ (Rio de Janeiro), "
    "dan ES (Espírito Santo) memiliki rasio keterlambatan tertinggi meskipun termasuk dalam kelompok state dengan volume "
    "pesanan besar, yang mengindikasikan adanya perbedaan performa logistik antar wilayah."
)

# FOOTER
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "Dashboard dibuat menggunakan Streamlit | Fokus pada penyampaian insight EDA"
    "</p>",
    unsafe_allow_html=True
)