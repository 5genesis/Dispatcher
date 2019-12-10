import openstack


class OSUtils():

    def connection(auth_url, region, project_name, username, password):
        return openstack.connect(
            auth_url=auth_url,
            project_name=project_name,
            username=username,
            password=password,
            user_domain_name="Default",
            project_domain_name="Default",
        )


    def upload_image(conn, f, disk_format="raw", container_format="bare"):
        # Build the image attributes and upload the image.
        image_attrs = {
            'name': f.filename,
            'filename': f.filename,
            'disk_format': disk_format,
            'container_format': container_format,
            'visibility': 'public',
        }
        return conn.image.create_image(**image_attrs)


    def import_image(conn):
        # Url where glance can download the image
        uri = 'https://download.cirros-cloud.net/0.4.0/' \
              'cirros-0.4.0-x86_64-disk.img'

        # Build the image attributes and import the image.
        image_attrs = {
            'name': 'prueba_borrar',
            'disk_format': 'qcow2',
            'container_format': 'bare',
            'visibility': 'public',
        }
        image = conn.image.create_image(**image_attrs)
        conn.image.import_image(image, method="web-download", uri=uri)

    def list_images(conn):
        for image in conn.image.images():
            print(image)

