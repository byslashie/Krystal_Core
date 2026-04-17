import pythonnet
pythonnet.load('netfx')
import clr
import System
from System.Security.Cryptography.X509Certificates import X509Store, X509Certificate2, OpenFlags, StoreLocation, StoreName, X509FindType

def main():
    print("Opening Cert Store (CurrentUser/My)...")
    store = X509Store(StoreName.My, StoreLocation.CurrentUser)
    store.Open(OpenFlags.ReadWrite)

    curr_time = System.DateTime.Now
    print(f"Current Time (System): {curr_time}")

    try:
        certs = store.Certificates
        print(f"Total Certs: {certs.Count}")

        to_remove = []

        for cert in certs:
            subject = cert.Subject
            if "Yuanta" in subject or "22206" in subject or "元大" in subject:
                print(f"\n--- Found Yuanta Cert ---")
                print(f"Subject: {subject}")
                print(f"Thumbprint: {cert.Thumbprint}")
                print(f"NotAfter: {cert.NotAfter}")
                
                # Check expiration
                if cert.NotAfter < curr_time:
                    print(f"⚠️ EXPIRED! (Expired on {cert.NotAfter})")
                    to_remove.append(cert)
                else:
                    print(f"✅ VALID (Expires on {cert.NotAfter})")

        if not to_remove:
            print("\nNo expired Yuanta certificates found.")
        else:
            print(f"\nPreparing to delete {len(to_remove)} expired certificates...")
            for cert in to_remove:
                print(f"Deleting Thumbprint: {cert.Thumbprint}")
                store.Remove(cert)
            print("Deletion complete.")

    finally:
        store.Close()
        print("\nStore closed.")

if __name__ == "__main__":
    main()
