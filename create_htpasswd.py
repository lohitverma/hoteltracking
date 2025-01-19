from passlib.apache import HtpasswdFile
import getpass

ht = HtpasswdFile(".htpasswd", new=True)
password = getpass.getpass("Enter password for admin: ")
ht.set_password("admin", password)
ht.save()
