with open("frontend/src/components/Header.tsx", "r") as f:
    content = f.read()

content = content.replace("""      {
        {
          name: "Fornecedores",
          description: "Ranking de empresas e notas fiscais",
          href: "/empresas",
        },
        name: "Métricas",
        href: "/metricas",""", """      {
        name: "Fornecedores",
        description: "Ranking de empresas e notas fiscais",
        href: "/empresas",
        icon: <Icons.Building />,
      },
      {
        name: "Métricas",
        href: "/metricas",""")

with open("frontend/src/components/Header.tsx", "w") as f:
    f.write(content)
