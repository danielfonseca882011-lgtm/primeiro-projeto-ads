# Projeto: Controle Financeiro
# Desenvolvedor: Daniel Fonseca
# Curso: Analise e Desenvolvimento de Sistemas

print("================================")
print("     CONTROLE FINANCEIRO")
print("================================")

saldo = 0

while True:
    print("\nMENU PRINCIPAL")
    print("1 - Adicionar receita")
    print("2 - Adicionar despesa")
    print("3 - Consultar saldo")
    print("4 - Sair")

    opcao = input("\nEscolha uma opcao: ")

    if opcao == "1":
        valor = float(input("Digite o valor da receita: R$ "))
        saldo += valor
        print("Receita adicionada com sucesso!")

    elif opcao == "2":
        valor = float(input("Digite o valor da despesa: R$ "))
        saldo -= valor
        print("Despesa registrada com sucesso!")

    elif opcao == "3":
        print(f"Seu saldo atual e: R$ {saldo:.2f}")

    elif opcao == "4":
        print("Obrigado por utilizar o sistema!")
        break

    else:
        print("Opcao invalida! Tente novamente.")