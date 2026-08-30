APX RETURN TO HUB

SUPER+E reinicia o Windows e regressa ao APX, porque o Linux Boot Manager
permanece em primeiro lugar na ordem UEFI. O helper interceta a combinação
antes do Explorer apenas enquanto está ativo; fora dele, WIN+E mantém o
comportamento normal do Windows.

O helper arranca oculto em segundo plano a cada início de sessão e volta a
tentar automaticamente se o hook de teclado ainda não estiver disponível.
O diagnóstico fica em %LOCALAPPDATA%\APX\ReturnToHub.log. Não é colocado
qualquer ícone APX no Ambiente de Trabalho.
