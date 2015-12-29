# WordPress/MySql/NGINX fabfile

This is a fabfile for [Fabric](https://github.com/fabric/fabric) that makes installing WordPress, MySQL or a blank NGINX server dirt simple.

## Caveats
- Your setup needs to be configured properly before this works. NGINX doesn't use the `sites-available/sites-enabled` setup out of the box, so you'll need to configure that.
- The MySQL function only stores the randomly created credentials in the wp-config file, so don't lose it.
- Expects a three character subdomain (www), it currently won't work if you're trying to set up a bare `http://example.com` domain

## Cool things
- It automatically creates a more secure wp-config.php file when you install WP. It creates and replaces the `salt` stuff, and it creates a randomly generated `wp_` prefix instead of the default.
- The script automatically grabs the latest stable tag from WordPress' [github mirror](http://github.com/WordPress/WordPress), which is cool.

## Usage

    # Installing wordpress
    fab -H <host> wordpress:<www.domain.com>

    # Creating new NGINX server
    fab -H <host> nginx:<www.domain.com>

## License
MIT Copyright (c) 2015 Dan Gayle
