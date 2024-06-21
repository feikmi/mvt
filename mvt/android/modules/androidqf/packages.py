# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021-2023 The MVT Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import logging
from typing import Optional
import json

from mvt.android.utils import (
    ROOT_PACKAGES,
    BROWSER_INSTALLERS,
    PLAY_STORE_INSTALLERS,
    THIRD_PARTY_STORE_INSTALLERS,
)

from .base import AndroidQFModule


class Packages(AndroidQFModule):
    """This module examines the installed packages in packages.json"""

    def __init__(
        self,
        file_path: Optional[str] = None,
        target_path: Optional[str] = None,
        results_path: Optional[str] = None,
        module_options: Optional[dict] = None,
        log: logging.Logger = logging.getLogger(__name__),
        results: Optional[list] = None,
    ) -> None:
        super().__init__(
            file_path=file_path,
            target_path=target_path,
            results_path=results_path,
            module_options=module_options,
            log=log,
            results=results,
        )

    def check_indicators(self) -> None:
        for result in self.results:
            if result["name"] in ROOT_PACKAGES:
                self.log.warning(
                    "Found an installed package related to "
                    'rooting/jailbreaking: "%s"',
                    result["name"],
                )
                self.detected.append(result)
                continue

            # Detections for apps installed via unusual methods
            if result["installer"] in THIRD_PARTY_STORE_INSTALLERS:
                self.log.warning(
                    'Found a package installed via a third party store (installer="%s"): "%s"',
                    result["installer"],
                    result["name"],
                )
            elif result["installer"] in BROWSER_INSTALLERS:
                self.log.warning(
                    'Found a package installed via a browser (installer="%s"): "%s"',
                    result["installer"],
                    result["name"],
                )
            elif result["installer"] == "null" and result["system"] is False:
                self.log.warning(
                    'Found a non-system package installed via adb or another method: "%s"',
                    result["name"],
                )
            elif result["installer"] in PLAY_STORE_INSTALLERS:
                pass

            if not self.indicators:
                continue

            ioc = self.indicators.check_app_id(result.get("name"))
            if ioc:
                result["matched_indicator"] = ioc
                self.detected.append(result)
                continue

            for package_file in result.get("files", []):
                ioc = self.indicators.check_file_hash(package_file["sha256"])
                if ioc:
                    result["matched_indicator"] = ioc
                    self.detected.append(result)

    def run(self) -> None:
        packages = self._get_files_by_pattern("*/packages.json")
        if not packages:
            self.log.error(
                "packages.json file not found in this androidqf bundle. Possibly malformed?"
            )
            return

        self.results = json.loads(self._get_file_content(packages[0]))
        self.log.info("Found %d packages in packages.json", len(self.results))
