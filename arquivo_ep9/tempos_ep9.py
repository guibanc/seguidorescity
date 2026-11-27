# Tempos do ep. 9, medidos na narração (narracao_ep9.wav, 103,9 s).
# L = (início, fim) de cada fala; KW = palavras-chave usadas pela animação.
L = [(0.22, 3.20), (3.89, 9.91), (10.50, 12.67), (13.12, 14.89), (15.41, 18.34), (18.88, 23.63), (24.31, 32.91), (33.50, 36.25),
     (36.96, 43.80), (44.35, 48.02), (48.72, 50.82), (51.31, 54.80), (55.45, 60.33), (60.93, 65.05), (65.79, 72.74), (73.43, 77.26),
     (78.01, 84.73), (85.56, 93.01), (93.71, 99.56), (100.16, 103.60)]
def at(i, f): a, b = L[i-1]; return round(a+(b-a)*f, 2)
KW = dict(
    fumaca=at(3, 0.75), fogo0=at(4, 0.2), FOGO=at(4, 0.82), baldes=at(5, 0.3), la=at(5, 0.7), apagou=at(6, 0.0), precisava=at(6, 0.7),
    fundado=24.91, caminhao=28.86, sirene=at(7, 0.6), banho=at(7, 0.78), reforma=at(8, 0.55),
    c73=38.67, c74=at(9, 0.5), c75=at(9, 0.64), c76=at(9, 0.78), ruaE=at(9, 0.9), ruaF=at(10, 0.05), c77=46.18, c78=at(10, 0.85),
    petshop=at(11, 0.75), cachorro=at(12, 0.6), gato=at(12, 0.78), galinha=at(12, 0.9),
    campeonato=at(13, 0.25), timecontra=57.49, torcida=at(13, 0.75),
    c14=at(14, 0.42), abriu=62.24+0.8, panfleto=65.79, discurso=69.22, briga=70.70, n777=at(15, 0.9),
    prometeu=at(16, 0.35), antes=75.59, destaque=78.01, discurso2=81.38, online=83.09,
    m800=at(18, 0.2), reservado=88.56, faltam=91.97,
    r780=at(19, 0.12), r78=at(19, 0.3), rbomb=97.53, rpet=98.82, link=100.16, votar=102.22)
DUR = 104.6
T = dict(titulo=(0.0, L[1][0]-0.1), recap=(L[1][0]-0.1, L[2][0]-0.3), fogo=(L[2][0]-0.3, L[6][0]-0.3),
         bombeiros=(L[6][0]-0.3, L[8][0]-0.3), casas=(L[8][0]-0.3, L[10][0]-0.3), petshop=(L[10][0]-0.3, L[12][0]-0.3),
         campeonato=(L[12][0]-0.3, L[13][0]-0.3), eleicao=(L[13][0]-0.3, L[15][0]-0.3), promessa=(L[15][0]-0.3, L[16][0]-0.3),
         destaque=(L[16][0]-0.3, L[17][0]-0.3), proximo=(L[17][0]-0.3, L[18][0]-0.3), resumo=(L[18][0]-0.3, L[19][0]-0.3),
         cta=(L[19][0]-0.3, DUR))
# contador: casas 73-76 na fala 9, 77-78 na fala 10
CK = [(0, 721), (KW['c73']-0.8, 721), (KW['c73'], 731), (KW['c74'], 741), (KW['c75'], 751), (KW['c76'], 761),
      (KW['ruaF'], 765), (KW['c77'], 771), (KW['c78'], 780)]
