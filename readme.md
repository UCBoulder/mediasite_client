# Mediasite Client

A Python class for interfacing with the Mediasite API to perform common actions.

## Prerequisites

Before you get started, make sure to install or create the following prerequisites:

* Python 3.x: [https://www.python.org/downloads/](https://www.python.org/downloads/)
* Python Requests Library (non-native library used for HTTP requests): [http://docs.python-requests.org/en/master/](http://docs.python-requests.org/en/master/)
* pandas: [https://github.com/pandas-dev](https://github.com/pandas-dev)
* pytz: [https://github.com/newvem/pytz](https://github.com/newvem/pytz)
* tzlocal: [https://github.com/regebro/tzlocal](https://github.com/regebro/tzlocal)

Additionally, within your Mediasite installation please prepare the following:

* A Mediasite user with operations "API Access" and "Manage Auth Tickets" (configurable within the Mediasite Management Portal)
* A Mediasite API key: [https://&lt;your-hostname&gt;/mediasite/api/Docs/ApiKeyRegistration.aspx](https://&lt;your-hostname&gt;/mediasite/api/Docs/ApiKeyRegistration.aspx)

## Special Notes

Mediasite API documentation can be found at the following URL (change the bracketed area to your site-specific base domain name): [http://&lt;your-hostname&gt;/mediasite/api/v1/$metadata](http://&lt;your-hostname&gt;/mediasite/api/v1/$metadata)

The Mediasite API makes heavy use of the ODATA standard for some requests (including the demo performed within this repo). For more docuemntation on this standard reference the following URL: [http://www.odata.org/documentation/odata-version-3-0/url-conventions/#requestingdata](http://www.odata.org/documentation/odata-version-3-0/url-conventions/#requestingdata)

Special note: programmatic creation of Mediasite weekly recurrences using the Mediasite API have bugs that sometimes cause inconsistent views or creation of recordings. Because of this, "weekly" recurrences are created using calculated one-time dates and times. This results in the schedule looking slightly different but appearing and recording correctly as per user-provided entry.

## Usage

1. Ensure prerequisites outlined above are completed.
1. Fill in necessary information within config/sample_config.json and rename to project specifics
1. Remove the text "_sample" from all config file
1. Use as needed within your Python applications 

## Example

	>>>import json
	>>>import assets.mediasite.controller as controller
	>>>config_file = open(r"c:\users\sgtpepper\desktop\mediasite_client\config\config.json")
    >>>config_data = json.load(config_file)
    >>>mediasite = controller.mediasite(config_data)
    >>>mediasite.recorder.gather_recorders()
    [{'name': 'RECORDER1', 'id': '111111111111111111111111111111'}, {'name': 'RECORDER2', 'id': '1111111111111111111111111111'}]

## License

MIT - See license.txt

## Notice

The project is made possible by open source software. Please see the following listing for software used and respective licensing information:

* Python 3 - PSF [https://docs.python.org/3/license.html](https://docs.python.org/3/license.html)
* Requests - Apache 2.0 [https://opensource.org/licenses/Apache-2.0](https://opensource.org/licenses/Apache-2.0)
* pandas - BSD 3-Clause [https://opensource.org/licenses/BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause)
* pytz - MIT [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)
* tzlocal - MIT [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)

