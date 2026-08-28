from flask import Flask, render_template, redirect, request
import pyodbc

app = Flask(__name__)
def conectar_banco():
    conexao = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost\\sqlexpress;"
        "DATABASE=SeuStyle;"
        "Trusted_Connection=yes;"
    )

    return conexao

carrinho = []
clientes = []


produtos = [
    {
        "id": 1,
        "nome": "Camiseta",
        "preco": 50.00,
        "imagem": "camiseta.jpg"
    },
    {
        "id": 2,
        "nome": "Calça Jeans",
        "preco": 120.00,
        "imagem": "calca.jpg"
    },
    {
        "id": 3,
        "nome": "Moletom",
        "preco": 90.00,
        "imagem": "moletom.jpg"
    }
]


@app.route("/")
def inicio():
    return render_template("index.html", produtos=produtos)


@app.route("/comprar/<int:id>")
def comprar(id):

    for produto in produtos:

        if produto["id"] == id:

            encontrado = False

            for item in carrinho:

                if item["id"] == id:
                    item["quantidade"] += 1
                    encontrado = True
                    break

            if not encontrado:
                novo_item = produto.copy()
                novo_item["quantidade"] = 1
                carrinho.append(novo_item)

            break

    return redirect("/carrinho")


@app.route("/carrinho")
def ver_carrinho():

    total = 0

    for produto in carrinho:

        produto["subtotal"] = (
            produto["preco"] * produto["quantidade"]
        )

        total += produto["subtotal"]

    return render_template(
        "carrinho.html",
        carrinho=carrinho,
        total=total
    )


@app.route("/aumentar/<int:id>")
def aumentar(id):

    for produto in carrinho:

        if produto["id"] == id:
            produto["quantidade"] += 1
            break

    return redirect("/carrinho")


@app.route("/diminuir/<int:id>")
def diminuir(id):

    for produto in carrinho:

        if produto["id"] == id:

            produto["quantidade"] -= 1

            if produto["quantidade"] <= 0:
                carrinho.remove(produto)

            break

    return redirect("/carrinho")


@app.route("/remover/<int:id>")
def remover(id):

    for produto in carrinho:

        if produto["id"] == id:
            carrinho.remove(produto)
            break

    return redirect("/carrinho")


# Página de cadastro
@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/cadastrar", methods=["POST"])
def cadastrar():

    nome = request.form["nome"]
    cpf = request.form["cpf"]
    email = request.form["email"]
    telefone = request.form["telefone"]
    endereco = request.form["endereco"]

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO Clientes
        (nome, cpf, email, telefone, endereco)
        VALUES (?, ?, ?, ?, ?)
    """, nome, cpf, email, telefone, endereco)

    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/clientes")

@app.route("/clientes")
def ver_clientes():

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM Clientes")

    clientes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template(
        "clientes.html",
        clientes=clientes
    )

if __name__ == "__main__":
    app.run(debug=True)