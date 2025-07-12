DROP TABLE IF EXISTS tempat_wisata;
DROP TABLE IF EXISTS pesanan;

CREATE TABLE tempat_wisata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    lokasi TEXT,
    harga INTEGER,
    deskripsi TEXT
);

CREATE TABLE pesanan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    jumlah INTEGER,
    tanggal TEXT,
    tempat_id INTEGER,
    FOREIGN KEY(tempat_id) REFERENCES tempat_wisata(id)
);