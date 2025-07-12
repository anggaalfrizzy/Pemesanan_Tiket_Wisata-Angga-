from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tiket_wisata_secret'
DATABASE = 'database/wisata.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    db = get_db()
    wisata = db.execute('SELECT * FROM tempat_wisata').fetchall()
    return render_template('index.html', wisata=wisata)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Login gagal. Coba lagi.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    db = get_db()
    try:
        pesanan = db.execute('''
            SELECT pesanan.*, COALESCE(tempat_wisata.nama, '[Wisata Dihapus]') as nama_wisata
            FROM pesanan
            LEFT JOIN tempat_wisata ON pesanan.tempat_id = tempat_wisata.id
            ORDER BY pesanan.tanggal DESC
        ''').fetchall()
        
        formatted_pesanan = []
        for p in pesanan:
            try:
                tanggal = datetime.strptime(p['tanggal'], '%Y-%m-%d').strftime('%d/%m/%Y')
            except:
                tanggal = p['tanggal']
            formatted_pesanan.append({**p, 'tanggal': tanggal})
            
        return render_template('pesanan.html', pesanan=formatted_pesanan)
    except Exception as e:
        flash(f'Error mengambil data pesanan: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/tambah-wisata', methods=['GET', 'POST'])
def tambah_wisata():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        db = get_db()
        try:
            nama = request.form['nama']
            lokasi = request.form['lokasi']
            harga = int(request.form['harga'])
            deskripsi = request.form['deskripsi']
            
            db.execute('''
                INSERT INTO tempat_wisata (nama, lokasi, harga, deskripsi) 
                VALUES (?, ?, ?, ?)
            ''', (nama, lokasi, harga, deskripsi))
            db.commit()
            flash('Tempat wisata berhasil ditambahkan!', 'success')
            return redirect(url_for('tempat_wisata'))
        except ValueError:
            flash('Harga harus berupa angka', 'danger')
        except Exception as e:
            flash(f'Gagal menambahkan: {str(e)}', 'danger')
    
    return render_template('tambah_wisata.html')

@app.route('/tempat-wisata')
def tempat_wisata():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    db = get_db()
    wisata = db.execute('SELECT * FROM tempat_wisata ORDER BY nama').fetchall()
    return render_template('tempat_wisata.html', wisata=wisata)

@app.route('/hapus-wisata/<int:id>')
def hapus_wisata(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    db = get_db()
    try:
        pesanan_terkait = db.execute('SELECT COUNT(*) FROM pesanan WHERE tempat_id = ?', (id,)).fetchone()[0]
        
        if pesanan_terkait > 0:
            flash('Tidak bisa menghapus karena ada pesanan terkait. Hapus pesanan terlebih dahulu.', 'warning')
        else:
            db.execute('DELETE FROM tempat_wisata WHERE id = ?', (id,))
            db.commit()
            flash('Tempat wisata berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Gagal menghapus: {str(e)}', 'danger')
    
    return redirect(url_for('tempat_wisata'))

@app.route('/hapus-pesanan/<int:id>')
def hapus_pesanan(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    db = get_db()
    try:
        db.execute('DELETE FROM pesanan WHERE id = ?', (id,))
        db.commit()
        flash('Pesanan berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Gagal menghapus pesanan: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/pesan/<int:id>', methods=['GET', 'POST'])
def pesan(id):
    db = get_db()
    try:
        wisata = db.execute('SELECT * FROM tempat_wisata WHERE id = ?', (id,)).fetchone()
        if not wisata:
            flash('Tempat wisata tidak ditemukan', 'danger')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            nama = request.form.get('nama', '').strip()
            jumlah = request.form.get('jumlah', '')
            tanggal = request.form.get('tanggal', '')
            
            if not nama or not jumlah or not tanggal:
                flash('Semua field harus diisi', 'danger')
                return render_template('pesan.html', wisata=wisata)
            
            try:
                jumlah = int(jumlah)
                if jumlah <= 0:
                    flash('Jumlah tiket harus lebih dari 0', 'danger')
                    return render_template('pesan.html', wisata=wisata)
                    
                db.execute('''
                    INSERT INTO pesanan (nama, jumlah, tanggal, tempat_id) 
                    VALUES (?, ?, ?, ?)
                ''', (nama, jumlah, tanggal, id))
                db.commit()
                flash('Tiket berhasil dipesan!', 'success')
                return redirect(url_for('index'))
            except ValueError:
                flash('Jumlah tiket harus angka', 'danger')
            except Exception as e:
                flash(f'Gagal memesan: {str(e)}', 'danger')
        
        return render_template('pesan.html', wisata=wisata)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        os.makedirs('database', exist_ok=True)
        with sqlite3.connect(DATABASE) as db:
            db.executescript(open('schema.sql').read())
    app.run(debug=True)