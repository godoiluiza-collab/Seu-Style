from flask import Flask, render_template, redirect, request
import pyodbc

app = Flask(__name__)


# Conexão com o banco de dados
def conectar_banco():

    conexao = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=sqlexpress;"
        "DATABASE=SeuStyle;"
        "UID=aluno;"
        "PWD=;"
    )

    return conexao


carrinho = []
clientes = []


# Buscar produtos
def buscar_produtos():

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, preco, categoria, estoque, imagem
        FROM Produtos
    """)

    produtos = []

    for produto in cursor.fetchall():

        produtos.append({
            "id": produto.id,
            "nome": produto.nome,
            "preco": float(produto.preco),
            "categoria": produto.categoria,
            "estoque": produto.estoque,
            "imagem": produto.imagem
        })

    cursor.close()
    conexao.close()

    return produtos


# Página inicial
@app.route("/")
def inicio():

    produtos = buscar_produtos()

    return render_template(
        "index.html",
        produtos=produtos
    )


# Comprar produto
@app.route("/comprar/<int:id>")
def comprar(id):

    produtos = buscar_produtos()

    for produto in produtos:

        if produto["id"] == id:

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute("""
                UPDATE Produtos
                SET estoque = estoque - 1
                WHERE id = ? AND estoque > 0
            """, id)

            if cursor.rowcount == 1:

                conexao.commit()

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

            cursor.close()
            conexao.close()

            break

    return redirect("/carrinho")


# Carrinho
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


# Aumentar quantidade
@app.route("/aumentar/<int:id>")
def aumentar(id):

    for produto in carrinho:

        if produto["id"] == id:

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute("""
                UPDATE Produtos
                SET estoque = estoque - 1
                WHERE id = ? AND estoque > 0
            """, id)

            if cursor.rowcount == 1:

                conexao.commit()
                produto["quantidade"] += 1

            cursor.close()
            conexao.close()

            break

    return redirect("/carrinho")


# Diminuir quantidade
@app.route("/diminuir/<int:id>")
def diminuir(id):

    for produto in carrinho:

        if produto["id"] == id:

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute("""
                UPDATE Produtos
                SET estoque = estoque + 1
                WHERE id = ?
            """, id)

            conexao.commit()

            produto["quantidade"] -= 1

            if produto["quantidade"] <= 0:

                carrinho.remove(produto)

            cursor.close()
            conexao.close()

            break

    return redirect("/carrinho")


# Remover produto
@app.route("/remover/<int:id>")
def remover(id):

    for produto in carrinho:

        if produto["id"] == id:

            quantidade = produto["quantidade"]

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute("""
                UPDATE Produtos
                SET estoque = estoque + ?
                WHERE id = ?
            """, quantidade, id)

            conexao.commit()

            carrinho.remove(produto)

            cursor.close()
            conexao.close()

            break

    return redirect("/carrinho")


# Finalizar pedido
@app.route("/finalizar")
def finalizar():
    total = 0

    for produto in carrinho:
        produto["subtotal"] = produto["preco"] * produto["quantidade"]
        total += produto["subtotal"]

    desconto = 0
    valor_desconto = 0

    return render_template(
        "finalizar.html",
        carrinho=carrinho,
        total=total,
        desconto=desconto,
        valor_desconto=valor_desconto
    )


# Página de cadastro
@app.route("/cadastro")
def cadastro():

    return render_template("cadastro.html")


# Cadastrar cliente e criar pedido
@app.route("/cadastrar", methods=["POST"])
def cadastrar():

    nome = request.form["nome"]
    cpf = request.form["cpf"]
    email = request.form["email"]
    telefone = request.form["telefone"]
    endereco = request.form["endereco"]

    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:

        # Cadastrar cliente
        cursor.execute("""
            INSERT INTO Clientes
            (nome, cpf, email, telefone, endereco)
            VALUES (?, ?, ?, ?, ?)
        """,
            nome,
            cpf,
            email,
            telefone,
            endereco
        )

        # Pegar ID do cliente
        cursor.execute("""
            SELECT id
            FROM Clientes
            WHERE cpf = ?
        """, cpf)

        cliente = cursor.fetchone()
        cliente_id = cliente[0]

        # Calcular total
        total = 0

        for produto in carrinho:

            produto["subtotal"] = (
                produto["preco"] * produto["quantidade"]
            )

            total += produto["subtotal"]

        # Criar pedido
        cursor.execute("""
            INSERT INTO Pedidos
            (cliente_id, total)
            OUTPUT INSERTED.id
            VALUES (?, ?)
        """,
            cliente_id,
            total
        )

        pedido_id = cursor.fetchone()[0]

        # Salvar itens do pedido
        for produto in carrinho:

            cursor.execute("""
                INSERT INTO ItensPedido
                (
                    pedido_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?)
            """,
                pedido_id,
                produto["id"],
                produto["quantidade"],
                produto["preco"],
                produto["subtotal"]
            )

        conexao.commit()

        cursor.close()
        conexao.close()

        # Mostrar a confirmação antes de limpar o carrinho
        resposta = render_template(
            "pedido_confirmado.html",
            carrinho=carrinho,
            total=total,
            nome=nome,
            pedido_id=pedido_id
        )

        # Limpar carrinho depois da compra
        carrinho.clear()

        return resposta

    except Exception as erro:

        conexao.rollback()

        cursor.close()
        conexao.close()

        raise erro


# Pedido confirmado
@app.route("/pedido-confirmado")
def pedido_confirmado():

    total = 0

    for produto in carrinho:

        produto["subtotal"] = (
            produto["preco"] * produto["quantidade"]
        )

        total += produto["subtotal"]

    return render_template(
        "pedido_confirmado.html",
        carrinho=carrinho,
        total=total
    )


# Visualizar clientes
@app.route("/clientes")
def ver_clientes():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            Clientes.id,
            Clientes.nome,
            Clientes.cpf,
            Clientes.email,
            Clientes.telefone,
            Clientes.endereco,
            COUNT(Pedidos.id) AS compras
        FROM Clientes
        LEFT JOIN Pedidos
            ON Clientes.id = Pedidos.cliente_id
        GROUP BY
            Clientes.id,
            Clientes.nome,
            Clientes.cpf,
            Clientes.email,
            Clientes.telefone,
            Clientes.endereco
        ORDER BY Clientes.nome
    """)

    clientes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("clientes.html", clientes=clientes)


# Estoque
@app.route("/estoque")
def estoque():

    produtos = buscar_produtos()

    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Produtos mais vendidos
    cursor.execute("""
        SELECT
            Produtos.nome,
            SUM(ItensPedido.quantidade) AS quantidade_vendida
        FROM ItensPedido
        INNER JOIN Produtos
            ON Produtos.id = ItensPedido.produto_id
        GROUP BY Produtos.nome
        ORDER BY quantidade_vendida DESC
    """)

    vendas = cursor.fetchall()

    # Vendas por categoria
    cursor.execute("""
        SELECT
            Produtos.categoria,
            SUM(ItensPedido.quantidade) AS quantidade_vendida
        FROM ItensPedido
        INNER JOIN Produtos
            ON Produtos.id = ItensPedido.produto_id
        GROUP BY Produtos.categoria
        ORDER BY quantidade_vendida DESC
    """)

    vendas_categoria = cursor.fetchall()

    # Total de produtos cadastrados
    cursor.execute("""
        SELECT COUNT(*)
        FROM Produtos
    """)

    total_produtos = cursor.fetchone()[0]

    # Total de unidades em estoque
    cursor.execute("""
        SELECT ISNULL(SUM(estoque), 0)
        FROM Produtos
    """)

    total_estoque = cursor.fetchone()[0]

    # Total de unidades vendidas
    cursor.execute("""
        SELECT ISNULL(SUM(quantidade), 0)
        FROM ItensPedido
    """)

    total_vendidos = cursor.fetchone()[0]

    # Produtos com estoque baixo
    cursor.execute("""
        SELECT COUNT(*)
        FROM Produtos
        WHERE estoque <= 2
    """)

    estoque_baixo = cursor.fetchone()[0]

    # Dados para o gráfico de estoque
    estoque_grafico = []

    for produto in produtos:

        estoque_grafico.append({
            "nome": produto["nome"],
            "estoque": produto["estoque"]
        })

    cursor.close()
    conexao.close()

    return render_template(
        "estoque.html",
        produtos=produtos,
        vendas=vendas,
        vendas_categoria=vendas_categoria,
        estoque_grafico=estoque_grafico,
        total_produtos=total_produtos,
        total_estoque=total_estoque,
        total_vendidos=total_vendidos,
        estoque_baixo=estoque_baixo
    )


# Diminuir estoque
@app.route("/diminuir-estoque/<int:id>")
def diminuir_estoque(id):

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE Produtos
        SET estoque = estoque - 1
        WHERE id = ? AND estoque > 0
    """, id)

    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/estoque")


# Iniciar sistema
if __name__ == "__main__":
    app.run(debug=True)

