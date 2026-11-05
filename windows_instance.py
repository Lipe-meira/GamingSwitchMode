"""Windows single-instance mutex."""
import ctypes
from ctypes import wintypes


# Código de erro do Windows para recurso já existente
ERROR_ALREADY_EXISTS = 183

def garantir_instancia_unica(nome_mutex: str):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    
    # Cria (ou abre) o Mutex nomeado
    # Importante: guarde o handle em uma variável global ou retorne-o
    # para que o garbage collector do Python não o destrua enquanto o app roda.
    mutex = kernel32.CreateMutexW(None, False, nome_mutex)
    ultimo_erro = ctypes.get_last_error()
    if not mutex:
        raise ctypes.WinError(ultimo_erro)
    
    if ultimo_erro == ERROR_ALREADY_EXISTS:
        # Já existe outra instância rodando!
        # Se quiser, pode exibir um messagebox rápido ou apenas sair em silêncio:
        kernel32.CloseHandle(mutex)
        return None
        
    return mutex

