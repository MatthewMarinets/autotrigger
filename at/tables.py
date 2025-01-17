"""
Verbose tables for data used by autotrigger
"""

native_functions: dict[tuple[str, str], tuple[str, list[str]]] = {
    ('Ntve', '00000001'): ('IntToFixed', ['00000001']),
    ('Ntve', '00000003'): ('FixedToInt', ['00000003']),
    ('Ntve', '00000030'): ('RegionCircle', ['00000049', '00000050']),
    ('Ntve', '00000045'): ('TimerGetElapsed', ['00000080']),
    ('Ntve', '00000056'): ('PlayerGroupEmpty', []),
    ('Ntve', '00000057'): ('PlayerGroupSingle', ['00000094']),
    ('Ntve', '00000076'): ('UnitLastCreated', []),
    ('Ntve', '00000077'): ('UnitKill', ['00000136']),
    ('Ntve', '00000079'): ('UnitGetType', ['00000138']),
    ('Ntve', '00000081'): ('UnitGetOwner', ['00000140']),
    ('Ntve', '00000083'): ('UnitGetPosition', ['00000144']),
    ('Ntve', '00000087'): ('UnitSetPropertyFixed', ['00000151', '00000152', '00000153']),
    ('Ntve', '00000089'): ('UnitIssueOrder', ['00000156', '00000157', '00000158']),
    ('Ntve', '00000097'): ('@return', ['00000488']),
    ('Ntve', '00000104'): ('UnitGroupEmpty', []),
    ('Ntve', '00000106'): ('UnitGroupClear', ['00000167']),
    ('Ntve', '00000111'): ('TriggerEnable', ['00000176', '00000177']),
    ('Ntve', '00000116'): ('TriggerExecute', ['00000182', '00000183', '00000184']),
    ('Ntve', '00000123'): ('@custom-script', []),
    ('Ntve', '00000128'): ('@binary-op', ['00000205', '00000206', '00000207']),
    ('Ntve', '00000129'): ('@binary-op', ['00000208', '00000209', '00000210']),
    ('Ntve', '00000132'): ('@and', []),
    ('Ntve', '00000133'): ('@or', []),
    ('Ntve', '00000136'): ('@set', ['00000219', '00000220']),
    ('Ntve', '00000137'): ('@if-else', []),
    ('Ntve', '00000139'): ('@return-default', []),
    ('Ntve', '00000179'): ('UnitGroupSelected', ['00000298']),
    ('Ntve', '00000192'): ('PlayerGroupAll', []),
    ('Ntve', '00000216'): ('UnitIsAlive', ['00000378']),
    ('Ntve', '00000233'): ('UnitCargoGroup', ['00000403']),
    ('Ntve', '00000242'): ('Wait', ['00000419', '00000420']),
    ('Ntve', '00000249'): ('CreepIsPresent', ['00000424']),
    ('Ntve', '00000255'): ('TechTreeUpgradeCount', ['00000446', '00000447', '448F39DC']),
    ('Ntve', '00000327'): ('@loop-unit-group', ['00000617', '00000618']),
    ('Ntve', '00000356'): ('RegionEntireMap', []),
    ('Ntve', '00000359'): ('UnitGroup', ['00000691', '00000692', '00000693', '00000695', '00000694']),
    ('Ntve', '00000388'): ('UnitPauseAll', ['00000771']),
    ('Ntve', '0343B95F'): ('ActorSend', ['BA752BDE', '397A96EB']),
    ('Ntve', '0366EE04'): ('UIDisplayMessage', ['0D120C33', 'A4C19F41', '78A54B52']),
    ('Ntve', '043D7B4F'): ('GameSetMissionTimePaused', ['4118216C']),
    ('Ntve', '09840835'): ('UnitBehaviorRemove', ['A6600060', 'EB47C731', 'A45406E1']),
    ('Ntve', '0B0A4FBE'): ('TechTreeUpgradeAllow', ['082DE673', '44F827BC', '87723663']),
    ('Ntve', '0B3D8934'): ('UISetTargetingOrder', ['DEEDBCBE', 'A21D1423', '0CA083F2', 'B35E76BE']),
    ('Ntve', '0C607001'): ('UserDataSetInt', ['01E73838', '1D32F9F4', '136F398B', '1D7CD16A', 'F5FDED27']),
    ('Ntve', '0E8A5B30'): ('UnitSetPosition', ['211C5A4E', '59E6F35F', 'B6EF4B7A']),
    ('Ntve', '0E8BB6F9'): ('CutsceneGoToBookmark', ['48F8AE5E', '13957982']),
    ('Ntve', '0F696993'): ('libNtve_gf_ActorLastCreated', []),
    ('Ntve', '0F7C3248'): ('TechTreeAbilityAllow', ['BFF56EB0', '9B01128C', '09B7BAEA']),
    ('Ntve', '10EBC0A6'): ('libNtve_gf_LastReplacedUnit', []),
    ('Ntve', '142FF15A'): ('UnitHasBehavior2', ['033DFD05', 'B29EDD13']),
    ('Ntve', '1AA9CCBB'): ('PlayerGetCooldown', ['AB179DA6', '0702F138']),
    ('Ntve', '1ABFD783'): ('TriggerEventParamName', ['12F3942B', '3A1A130B']),
    ('Ntve', '1E7539AD'): ('VisResetFoWAlpha', ['76A4155D']),
    ('Ntve', '2002EBDA'): ('UserDataGetText', ['949B145C', '5BD5B82E', '8F358B0C', '908810FE']),
    ('Ntve', '20E3B9BE'): ('DialogLastCreated', []),
    ('Ntve', '20E3B9BE'): ('DialogLastCreated', []),
    ('Ntve', '30000000'): ('libNtve_gf_PauseUnit', ['90000000', '01000000']),
    ('Ntve', '405648E4'): ('libNtve_gf_SetDialogItemHotkey', ['5D1349DE', 'A8AA8DF0', '74744039']),
    ('Ntve', '43F16BA5'): ('OrderTargetingPoint', ['B796880B', '32BBED47']),
    ('Ntve', '4A703103'): ('libNtve_gf_GlobalCinematicSetting', ['E095DC31']),
    ('Ntve', '4AB42F83'): ('DialogControlLastCreated', []),
    ('Ntve', '4C8D7F8C'): ('UnitTypeGetName', ['4E1379C9']),
    ('Ntve', '4DE06797'): ('VisGetFoWAlpha', ['E68EF192']),
    ('Ntve', '4F8CE2E5'): ('DialogControlSendAnimationEvent', ['DA6C315F', '4716794C', 'EAA6652D']),
    ('Ntve', '51260275'): ('ActorFromDialogControl', ['58CBF71C']),
    ('Ntve', '51A273F5'): ('TechTreeUnitAllow', ['B15D29C1', 'BC66D9AD', 'C26556EA']),
    ('Ntve', '55C79F96'): ('StringToText', ['30693AA2']),
    ('Ntve', '5870F9D1'): ('@TriggerAddEventGeneric', []),
    ('Ntve', '59BA1DDF'): ('Order', ['C2F687E6']),
    ('Ntve', '62157B3C'): ('libNtve_gf_SetDialogItemRenderPriority', ['75814CF4', '777E8E74', '6877165F']),
    ('Ntve', '62180C0B'): ('GameSetGlobalTimeScale', ['A359ECCE']),
    ('Ntve', '62292946'): ('CameraSetData', ['649E72C5', 'A0D33EFB']),
    ('Ntve', '6263AB61'): ('UnitCreateEffectPoint', ['4A43AFC2', '0054BBD3', 'AD458092']),
    ('Ntve', '62FBB9DC'): ('libNtve_gf_SetDialogItemAnimationTime', ['2D5EFCEE', '27F7AB79', '217470F7']),
    ('Ntve', '6A72FDF0'): ('libNtve_gf_CreateActorAtPoint', ['A0E0A756', '9B32F396']),
    ('Ntve', '6B296A7A'): ('UnitSetState', ['204235DD', 'ABC3F662', '2DB2B028']),
    ('Ntve', '6BF56043'): ('Floor', ['34D76022']),
    ('Ntve', '6E473B27'): ('libNtve_gf_SetDialogItemUnit', ['B2C87DA3', '48C25348', '44953A8B']),
    ('Ntve', '71596144'): ('@while', []),  # conditional while, 71596144
    ('Ntve', '72C1FB76'): ('DialogSetVisible', ['CB9F19F9', 'FF091149', '25A88BC6']),
    ('Ntve', '73C0339B'): ('UnitCreateEffectUnit', ['2BB8CB05', '9A7F392A', '88375332']),
    ('Ntve', '7B4A4D9D'): ('@@break;', []),
    ('Ntve', '7E8F82B1'): ('DialogSetFullscreen', ['509A05AA', '2528D993']),
    ('Ntve', '83B4BF45'): ('UnitGroupCount', ['62D9DA63', '4A5B3C88']),
    ('Ntve', '8518EA3D'): ('libNtve_gf_UnitIsPaused', ['BAD9EC09']),
    ('Ntve', '862673FA'): ('libNtve_gf_RestoreUnitSelection', ['077FA486']),
    ('Ntve', '86E40471'): ('@add', ['174E8B8C', 'BD48D330']),
    ('Ntve', '8C4DB610'): ('UISetDragSelectEnabled', ['6B845DD3', 'B5842312']),
    ('Ntve', '8EDD3557'): ('UISetMode', ['AE2D0D80', '5328E238', '31F1731E']),
    ('Ntve', '8F55F540'): ('OrderSetAutoCast', ['AD00B0D1', 'F2A2EEEC']),
    ('Ntve', '8F6FB1B4'): ('PortraitGetTriggerControl', ['73F4F5D5']),
    ('Ntve', '9152ECEB'): ('UnitRevive', ['5DBDA2A4']),
    ('Ntve', '9372FA34'): ('CutsceneSetTime', ['555CB712', '222DB034']),
    ('Ntve', '9435D821'): ('UnitGroupAdd', ['BE7DBEA1', '58E3C3B3']),
    ('Ntve', '95EAE029'): ('PlayerAddCooldown', ['A0583248', 'C7ADDBA0', '5C3CC684']),
    ('Ntve', '9A69046F'): ('@unknown9A69046F', ['8804B4EE', 'A9AFAEEB']),
    ('Ntve', '9B76E7C9'): ('TriggerSendEvent', ['EFE9F3E0']),
    ('Ntve', '9C391799'): ('DialogSetImageVisible', ['2B74049D', '14A0F8BA']),
    ('Ntve', '9D7786E5'): ('libNtve_gf_ReviveOrderWithNoTarget', ['C455207D', '6555F86E']),
    ('Ntve', '9F8EF8FB'): ('libNtve_gf_SetUpgradeLevelForPlayer', ['C7188352', '7E5035EE', '3BFEECBB']),
    ('Ntve', 'A03D3C7F'): ('UnitAbilityAdd', ['6942A4C8', '827DBADE']),
    ('Ntve', 'A0F31305'): ('@binary-op-statement-eq', ['7B3B0884', '5BFF7323', '6725C0EB']),
    ('Ntve', 'A7BB52AE'): ('PlayerType', ['00CB7424']),
    ('Ntve', 'A8732F20'): ('UnitGroupAddUnitGroup', ['32E1F427', '320F19A2']),
    ('Ntve', 'AB4663C2'): ('PlayerCreateEffectPoint', ['EA2CBB1A', 'FF6AF0FE', '01D6D660']),
    ('Ntve', 'ABD41ECF'): ('UnitHasBehavior', ['E163785B', 'D54684BD']),
    ('Ntve', 'AE4C1D89'): ('libNtve_gf_SetDialogItemUnitGroup', ['F003757A', '573243B7', '4DAA6EAF']),
    ('Ntve', 'B525B112'): ('@loop-player-group', ['A4B226A9', '857209C7']),
    ('Ntve', 'B71342F4'): ('DialogControlSetSize', ['C0DC5AAF', '4DDDAD3E', '0FDDC614', '6BC1C60F']),
    ('Ntve', 'BA583993'): ('libNtve_gf_SetDialogItemText', ['9EA7E372', '3B39C02D', '64290A01']),
    ('Ntve', 'BAEAC6C3'): ('libNtve_gf_ConvertUnitToUnitGroup', ['E208E60F']),
    ('Ntve', 'BC622053'): ('AITimePause', ['90FC545F']),
    ('Ntve', 'BC830FBE'): ('UnitGroupClosestToPoint', ['A9028457', 'CC2C842E']),
    ('Ntve', 'C0083258'): ('@if-elseif', []),
    ('Ntve', 'C15B101F'): ('PortraitUseTransition', ['91DA736E', '38941669']),
    ('Ntve', 'C439C375'): ('@eq', ['ABB380C4', '51567265', '4A15EC5F']),
    ('Ntve', 'C47C0524'): ('UnitBehaviorAdd', ['2E722704', '9A6B09E3', '02BBDCC1', '6F19F7ED']),
    ('Ntve', 'C560675A'): ('CutscenePlay', ['2391A8BE']),
    ('Ntve', 'C609209E'): ('DialogControlFadeTransparency', ['FF308E41', 'B6DEBC8D', '1212BC53', '9C5709DF']),
    ('Ntve', 'C65CC121'): ('UnitGetPropertyFixed', ['9ADE2B3B', 'D1035B0C', 'D006774F']),
    ('Ntve', 'C8CCD88A'): ('libNtve_gf_SetDialogItemModel', ['B01B0668', '4EB0A82E', 'D76A395B']),
    ('Ntve', 'CACCC2D8'): ('PlayerSetDifficulty', ['80DD7129', '2604D0EB']),
    ('Ntve', 'CC29332F'): ('DialogControlHookupStandard', ['06C1424C', 'AEF92396']),
    ('Ntve', 'CEDAB9C3'): ('@while', []),  # while-true, CEDAB9C3
    ('Ntve', 'D8957FF3'): ('DialogControlGetWidth', ['2D63926F', '6E9B1751']),
    ('Ntve', 'DB01ECDC'): ('@binary-op-statement', ['504494F0', '027F6EEF', '61958720']),
    ('Ntve', 'DD095653'): ('@unknownDD095653', ['0DE50046', '9ED4CC3D']),
    ('Ntve', 'E3741424'): ('libNtve_gf_PlayerRemoveCooldown', ['32A379D7', 'A4A109ED']),
    ('Ntve', 'E37ACA0E'): ('DialogControlSetVisible', ['21F36F40', '0EAACCBD', '3A302059']),
    ('Ntve', 'E48A04F2'): ('libNtve_gf_SetDialogItemAcceptMouse', ['51018031', 'D93A3681', 'CE765C0D']),
    ('Ntve', 'E6F8D690'): ('CutsceneGetTriggerControl', ['1E9E9A97']),
    ('Ntve', 'B975E43B'): ('VisSetFoWAlpha', ['9CE1B033', '6BA700E6']),
    ('Ntve', 'E92E544E'): ('libNtve_gf_CinematicMode', ['C016C6E2', '8F9FC828', '5755FC77']),
    ('Ntve', 'EAC465A1'): ('IntToText', ['D125FE97']),
    ('Ntve', 'EEDB2448'): ('ModI', ['7438F000', '1F52348B']),
    ('Ntve', 'EEFB5A8F'): ('GameSetSpeedValue', ['60713155']),
    ('Ntve', 'EF6279C8'): ('libNtve_gf_SetDialogItemCutscene', ['8981CFFF', '98636F14', '1C46AA0F']),
    ('Ntve', 'F1C17BBA'): ('DataTableSetInt', ['22B82CD9', 'EACCC6EF', '9E6F0FCC']),
    ('Ntve', 'F247156C'): ('libNtve_gf_CreateUnitsWithDefaultFacing', ['6A3CFF43', 'D43CB595', 'A927C67A', 'FF0C620E', '23D48FEC']),
    ('Ntve', 'F4B5BEE7'): ('DialogDestroy', ['C5AA206D']),
    ('Ntve', 'F6F9120D'): ('OrderTargetingUnit', ['BF82A2BC', '402665EE']),
    ('Ntve', '83BEEF42'): ('UnitBehaviorSpawn', ['A218DD60', 'B40206F9', '80B18769']),
    ('Ntve', '90CBEC01'): ('UnitGroupRemove', ['3CACD790', '834C89B2']),
    ('Ntve', '0805CD83'): ('UserDataInstance', ['7D8F2AA7', '68F69FB9']),
    ('Ntve', 'F7CE0B02'): ('UnitAbilityRemove', ['5CB032FB', 'BB764B81']),
    ('Ntve', 'AEBDE1ED'): ('ActorFromPortrait', ['3526B963']),
    ('Ntve', 'A5822235'): ('libNtve_gf_ClearPortraitAnimation', ['524B077D', '859D4A8F']),
    ('Ntve', '3F7D22D8'): ('libNtve_gf_PortraitSetAnim', ['32FCBFE6', '1D99FDD4', '523262A3', '1C7D9763', '9E5DCBF3']),
    ('Ntve', '00000383'): ('CatalogFieldValueGet', ['00000747', '00000748', '00000749', '00000750']),
    ('Ntve', '0154BFCA'): ('AbsI', ['3296B263']),
    ('Ntve', '00000155'): ('PlayerRace', ['00000248']),
    ('Ntve', '00000175'): ('UnitSelect', ['00000289', '00000290', '00000291']),
    ('Ntve', '00000027'): ('DistanceBetweenPoints', ['00000043', '00000044']),
    ('Ntve', '15E6A048'): ('UnitGetPropertyInt', ['675568F7', '8C622220', 'D04C0973']),
    ('Ntve', 'FC63B7AA'): ('', ['86234016']),

    ('Ntve', '397B15D6'): ('DialogControlHookup', ['4CA13C57', 'ACAA7C6B', '2147B27F']),
    ('Ntve', '5C08CD1C'): ('DialogControlCreateFromTemplate', ['E9FC58F5', 'EF551CD2', 'B68F0E3F']),
    ('Ntve', 'EE08EB84'): ('DialogControlSetAnimationTime', ['69BB17A6', 'EC715556', '2ED142AD', 'D5AA22FC']),
    ('Ntve', 'C835E90F'): ('libNtve_gf_UnitCreateFacingPoint', ['C110B88E', 'FDDBA4C9', '8F560A49', '6F9C2EF9', '7C15E2E4', '940F8CDA']),
    ('Ntve', '5084725D'): ('@upgrade-for-each-player', ['42AB3EFD']),    
    ('Ntve', '00000022'): ('Point', ['00000034', '00000035']),
    ('Ntve', '00000042'): ('TimerStart', ['00000073', '00000074', '00000075', '00000076']),
    ('Ntve', 'E89F1335'): ('@wait-for-condition', ['9C4402E6', '353DD7DE']),
    ('Ntve', '9755B9B4'): ('CameraSetValue', ['3E443D29', '1FCE2373', 'E704EBDF', 'A9ABC6A5', '53CA387A', 'BC825D28']),
    ('Ntve', '00000349'): ('@loop-n', ['00000677']),
    ('Ntve', 'C4DC760C'): ('@for-unit-in-group', ['F96B466D']),
    ('Ntve', '66474248'): ('@loop-player-group-range', ['F13E2CDE', 'C25E6187', 'F3144A4A', '8CB41668']),
    ('Ntve', '91C49196'): ('@switch', ['B4ACF12A']),
    ('Ntve', '00000118'): ('TriggerDebugOutput', ['C3CF50B0', '00000186', '00000187']),
    ('Ntve', '2CA88AC8'): ('libNtve_gf_SetDialogItemAnimationDuration', ['2ED34F4B', '3C9FCFA5', '60AC1A9B']),
    ('Ntve', '137A7BD8'): ('@unknown137A7BD8', ['709E9CD8', 'E983DE04']),
    ('Ntve', '160D3874'): ('@unknown160D3874', ['309FBBA0', '95E83C8C']),
    ('Ntve', '1B79DE77'): ('UserDataGetInt', ['A65030BE', 'F33ACFAA', '344B79F1', 'ECEA677C']),
    ('Ntve', '2DCE16C1'): ('@unknown2DCE16C1', ['027BBA1F', '143276AA']),
    ('Ntve', '3EC64613'): ('@unknown3EC64613', ['6116B0AF']),
    ('Ntve', '63083C14'): ('@unknown63083C14', ['3297DA07', 'B8BA9F0C']),
    ('Ntve', '6C39A0DF'): ('@unknown6C39A0DF', ['972A74CB', '5AC69524', '1EC7B7A1', '5908CAE6', 'EF0CF6FF', '9329BF02']),
    ('Ntve', '752159DD'): ('CreepModify', ['A098DF9A', 'BDE0AA6B', 'E97C11AF', '733A38D6']),
    ('Ntve', '80A31841'): ('@unknown80A31841', ['FBEE4B1F', '6FCB7975']),
    ('Ntve', 'A89BD9B9'): ('@unknownA89BD9B9', ['794EB233', '55A0DC19']),
    ('Ntve', 'F09DDBE5'): ('@unknownF09DDBE5', ['07D5D1D2', '199392D9', 'DBC70FFE', '7CCFF85E', '308734A1', '3169D445']),
    ('Ntve', 'F5662180'): ('libNtve_gf_ReplaceUnit', ['4C513242', 'C0271FCD', 'C9FA4297']),
    ('Ntve', 'F6DFE3E7'): ('UnitSetInfoText2', ['83FCF1CB', 'C8442849']),
    ('Ntve', 'BD9AF7D6'): ('DialogCreate', ['0A54556D', '2E6CF4F4', 'F4B2815D', 'D323187B', '6580A7BB', 'AB235258']),
    ('Ntve', 'CFF28424'): ('libNtve_gf_CreateDialogItemImage', ['E9B30437', 'C75A054C', '5359B79B', 'F603F646', 'F3BF60DA', '350AB972', '650E7611', 'A89683C6', '38769A6B', 'F2BAFF50', 'C08BF45E', 'C1B54AA4']),
    ('Ntve', '6ECCAD6C'): ('libNtve_gf_PlayAnimation', ['7829666A', '04C656AE', 'AAC1B96D', '2BAAA91B', 'E98DC791']),
    ('Ntve', 'D5F9189A'): ('libNtve_gf_SetDialogItemImage', ['9735F524', '24AFC666', 'E9EB3E48']),
    ('Ntve', '29AFAB1F'): ('UnitOrderIsValid', ['BDA13229', 'BFD54244']),
    ('Ntve', '3A1227AB'): ('@unknown3A1227AB', ['9A8F1093']),
    ('Ntve', '00000078'): ('@unknown00000078', ['00000137']),
    ('Ntve', 'E1552C18'): ('@unknownE1552C18', ['5A8D5B9F', '8FF77F87']),
    ('Ntve', '19CE733E'): ('@loop-var', []),
    # ('Ntve', ''): ('', []),

}


native_presets = {
    '00000030': 'nullabilcmd',  # abilcmd
    '79264E1B': 'null',  # OrderTargetingUnit, abilcmd
    'C7E46DC5': 'null',  # abilcmd
    '00000231': 'null',  # string / UnitGroup type
    'F5E3F3AD': 'null',  # region
    'C9DCA6C0': 'null',  # behavior
    '99AB77FB': 'null',  # order
    'D6EA4D09': 'null',  # unit
    '568CBBF1': 'null',  # point
    '00000021': 'true',  # CreepModify
    '00000063': 'true',
    '00000065': 'true',
    '00000067': 'true',
    '00000106': 'true',
    '00000108': 'true',  # UnitSelect
    '00000115': 'true',
    '00000120': 'true',
    '440EEF91': 'true',  # DialogCreate
    '00000022': 'false',  # CreepModify
    '74ABD11F': 'false',  # CreepModify
    '00000064': 'false',
    '00000068': 'false',
    '00000072': 'false',
    '00000107': 'false',
    '00000116': 'false',
    '00000121': 'false',
    '00000545': 'false',
    '085729C5': 'false',
    '0EA75E11': 'false',
    '00000087': '*',
    '00000088': '/',
    '00000538': 'true',
    '1468BD55': '0',
    '1E7A4625': '==',
    '500677B2': '!=',
    '40567BEE': '>',
    '684CA9CE': '<',
    'B128CB9A': '>=',
    'E123C832': '<=',
    '00000085': '+',
    '00000086': '-',
    'AEB4446D': '1',  # TriggerDebugOutput
    '4D47A35C': '-1',
    '3A57447B': 'Color(100,100,100)',
    '7C2BF97A': 'c_anchorBottom',
    '8094C4C1': 'c_anchorCenter',
    '22006C37': 'c_animNameDefault',
    '00000125': 'c_cameraValueDistance',
    '00000126': 'c_cameraValuePitch',
    '00000533': 'c_gameCatalogUnit',
    '8EDBFCEC': 'c_gameSpeedSlower',
    '297085AC': 'c_gameSpeedSlow',
    'FD093194': 'c_gameSpeedNormal',
    'B10EB399': 'c_gameSpeedFast',
    'D85EAE19': 'c_gameSpeedFaster',
    '3CBD992A': 'c_hotkeyHeroSelect0',
    'E58F114B': 'c_hotkeyHeroSelect1',
    'B76A7F2A': 'c_invalidDialogId',
    'FAC49C47': 'c_invalidDialogControlId',
    '362A0F1D': 'c_invalidPingId',
    '89CC0A21': 'c_messageAreaChat',
    '00000039': 'c_orderQueueReplace',
    '00000041': 'c_orderQueueAddToFront',
    '2999701E': 'c_playerAny',
    '477F1309': 'c_playerTypeUser',
    'DA6F0821': 'c_techCountQueuedOrBetter',
    'D78D6018': 'c_techCountCompleteOnly',
    '00000012': 'c_timeReal',
    '00000013': 'c_timeGame',
    'D88ACDB5': 'c_transitionDurationImmediate',
    'F4355835': 'c_transitionDurationDefault',
    '74C50A96': 'c_triggerControlTypeButton',
    'C4F1C285': 'c_triggerControlTypeLabel',
    '67A829E2': 'c_triggerControlTypePanel',
    '24F29C4B': 'c_triggerControlTypePortrait',
    'D1770C6B': 'c_triggerControlTypeUnitTarget',
    '0E62911C': 'c_unitCountAlive',
    'E85564CA': 'c_unitCreateIgnorePlacement',
    'E66C6645': 'c_unitPropCurrent',
    '00000031': 'c_unitPropEnergy',
    'B02395AB': 'c_unitPropEnergy',
    '00000032': 'c_unitPropEnergyMax',
    'D41421BB': 'c_unitPropEnergyPercent',
    'E93DFC69': 'c_unitPropEnergyPercent',
    '00000415': 'c_unitPropEnergyRegen',
    '5A040EDD': 'c_unitPropEnergyRegen',
    'F65D16B2': 'c_unitPropLife',
    '36468651': 'c_unitPropLifePercent',
    '00000416': 'c_unitPropLifeRegen',
    'DA0B238E': 'c_unitPropLifeRegen',
    '35EA11B2': 'c_unitPropResources',
    'F6D2A277': 'c_unitPropResources',
    '702A7D05': 'c_unitPropXP',
    '3667B35B': 'c_unitStateSelectable',
    'EFBDA3CB': 'c_uiModeConsole',
    'B2D12F4E': 'c_uiModeFullscreen',
    '5BABA18D': 'libNtve_ge_ReplaceUnitOptions_NewUnitsDefault',
    'AC8DD36D': 'libNtve_ge_ReplaceUnitOptions_OldUnitsRelative',
}


target_filter_value = {
    'Self': 0,
    'Player': 1,
    'Ally': 2,
    'Neutral': 3,
    'Enemy': 4,
    'Air': 5,
    'Ground': 6,
    'Light': 7,
    'Armored': 8,
    'Biological': 9,
    'Robotic': 10,
    'Mechanical': 11,
    'Psionic': 12,
    'Massive': 13,
    'Structure': 14,
    'Hover': 15,
    'Heroic': 16,
    'User1': 17,
    'Worker': 18,
    'RawResource': 19,
    'HarvestableResource': 20,
    'Missile': 21,
    'Destructible': 22,
    'Item': 23,
    'Uncommandable': 24,
    'CanHaveEnergy': 25,
    'CanHaveShields': 26,
    'PreventDefeat': 27,
    'PreventReveal': 28,
    'Buried': 29,
    'Cloaked': 30,
    'Visible': 31,
    'Stasis': 32,
    'UnderConstruction': 33,
    'Dead': 34,
    'Revivable': 35,
    'Hidden': 36,
    'Hallucination': 37,
    'Invulnerable': 38,
    'HasEnergy': 39,
    'HasShields': 40,
    'Benign': 41,
    'Passive': 42,
    'Detector': 43,
    'Radar': 44,
    'Stunned': 45,
    'Summoned': 46,
    'Unstoppable': 47,
    'Outer': 48,
    'Resistant': 49,
    'Silenced': 50,
    'Dazed': 51,
    'MapBoss': 52,
    'Decaying': 53,
    'Raisable': 54,
    'HeroUnit': 55,
    'NonBuildingUnit': 56,
    'GroundUnit': 57,
    'AirUnit': 58,
    'Powerup': 59,
    'PowerupOrItem': 60,
    'NeutralHostile': 61,
}

default_return_values = {
    'bool': 'true',
    'int': '0',
    'string': 'null',
}

# types = {
    # 'actor'
    # 'actorscope'
    # 'abilcmd'
    # 'aifilter'
    # 'aidef'
    # 'aidefwave'
    # 'attributegame'
    # 'attributeplayer'
    # 'attributevalue'
    # 'anynumber'
    # 'anyvariable'
    # 'anypreset'
    # 'anycompare'
    # 'anygamelink'
    # 'animlengthquery'
    # 'bool'
    # 'bank'
    # 'bitmask'
    # 'camerainfo'
    # 'conversation'
    # 'convline'
    # 'convstateindex'
    # 'catalogentry'
    # 'catalogfieldname'
    # 'catalogfieldpath'
    # 'catalogscope'
    # 'color'
    # 'control'
    # 'cinematic'
    # 'cooldown'
    # 'charge'
    # 'doodad'
    # 'datatable'
    # 'datetime'
    # 'difficulty'
    # 'dialog'
    # 'effecthistory'
    # 'fixed'
    # 'fontstyle'
    # 'filepath'
    # 'gameoption'
    # 'gameoptionvalue'
    # 'int'
    # 'layoutframe'
    # 'layoutframerel'
    # 'marker'
    # 'modelanim'
    # 'objective'
    # 'order'
    # 'preset'
    # 'point'
    # 'playergroup'
    # 'playercolor'
    # 'portrait'
    # 'path'
    # 'ping'
    # 'planet'
    # 'region'
    # 'return'
    # 'revealer'
    # 'reference'
    # 'reply'
    # 'sameas'
    # 'sameasparent'
    # 'sound'
    # 'soundlink'
    # 'timer'
    # 'timeofday'
    # 'text'
    # 'trigger'
    # 'transmission'
    # 'transmissionsource'
    # 'targetfilter'
    # 'unit'
    # 'unitgroup'
    # 'unitfilter'
    # 'userinstance'
    # 'userfield'
    # 'water'
    # 'wave'
    # 'waveinfo'
    # 'wavetarget'
# }
