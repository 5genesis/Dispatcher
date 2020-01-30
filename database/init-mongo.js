db.createUser(
    {
        user: "5genesis",
        pwd: "5genesisPASS",
        roles: [
            {
                role: "readWrite",
                db: "experimentsdb"
            }
        ]
    }
)

